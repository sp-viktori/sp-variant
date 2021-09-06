//! Yet another INI-like file parser.
//!
//! This one is specifically written for the somewhat simplified format of
//! the os-release file as found in recent Linux distributions.

use std::collections::HashMap;
use std::error;
use std::fs;
use std::path;

quick_error! {
    /// An error that occurred during parsing.
    #[derive(Debug)]
    enum YAIError {
        /// A backslash at the end of the line.
        BackslashAtEnd(line: String) {
            display("Backslash at the end of the {:?} os-release line", line)
        }
        /// An invalid line in the /etc/os-release file.
        BadLine(line: String) {
            display("Unexpected os-release line {:?}", line)
        }
        /// A quoted value contains the quote character.
        QuoteInQuoted(line: String) {
            display("The value in the {:?} os-release line contains the quote character", line)
        }
        /// Mismatched open/close quotes.
        MismatchedQuotes(line: String) {
            display("Mismatched open/close quotes in the {:?} os-release line", line)
        }
    }
}

const RE_LINE: &str = "(?x)
    ^ (?:
        (?P<comment> \\s* (?: \\# .* )? )
        |
        (?:
            (?P<varname> [A-Za-z0-9_]+ )
            =
            (?P<full>
                (?P<oquot> [\"'] )?
                (?P<quoted> .*? )
                (?P<cquot> [\"'] )?
            )
        )
    ) $
";

fn parse_line(
    re_line: &regex::Regex,
    line: &str,
) -> Result<Option<(String, String)>, Box<dyn error::Error>> {
    match re_line.captures(line) {
        Some(caps) => {
            if caps.name("comment").is_some() {
                return Ok(None);
            }
            let oquot = caps.name("oquot").map(|value| value.as_str());
            let cquot = caps.name("cquot").map(|value| value.as_str());
            let varname = &caps["varname"];
            let quoted = &caps["quoted"];

            if let Some("'") = oquot {
                if quoted.contains('\'') {
                    return Err(Box::new(YAIError::QuoteInQuoted(line.to_string())));
                }
                if cquot != oquot {
                    return Err(Box::new(YAIError::MismatchedQuotes(line.to_string())));
                }
                return Ok(Some((varname.to_string(), quoted.to_string())));
            }

            let mut quoted = match oquot {
                Some("\"") => {
                    if cquot != oquot {
                        return Err(Box::new(YAIError::MismatchedQuotes(line.to_string())));
                    }
                    quoted
                }
                Some(other) => panic!("YAI parse_line: {:?}: oquot {:?}", line, other),
                None => &caps["full"],
            }
            .to_string();
            let mut res: String = String::new();
            while !quoted.is_empty() {
                match quoted.find('\\') {
                    Some(idx) => match quoted.get(idx + 1..idx + 2) {
                        Some(qchar) => {
                            res.push_str(&quoted[..idx]);
                            res.push_str(qchar);
                            quoted.replace_range(..idx + 2, "");
                        }
                        None => return Err(Box::new(YAIError::BackslashAtEnd(line.to_string()))),
                    },
                    None => {
                        res.push_str(&quoted);
                        quoted.clear();
                    }
                }
            }
            Ok(Some((varname.to_string(), res)))
        }
        None => Err(Box::new(YAIError::BadLine(line.to_string()))),
    }
}

/// Parse a file, return a name: value mapping.
pub fn parse<P: AsRef<path::Path>>(
    path: P,
) -> Result<HashMap<String, String>, Box<dyn error::Error>> {
    let contents = fs::read_to_string(path)?;
    let re_line = regex::Regex::new(RE_LINE).unwrap();
    let mut res = HashMap::new();
    for line in contents.lines() {
        if let Some((name, value)) = parse_line(&re_line, line)? {
            res.insert(name, value);
        }
    }
    Ok(res)
}

#[cfg(test)]
mod tests {
    use std::error;
    use std::fs;

    const LINES_BAD: [&str; 5] = [
        "NAME='",
        "NAME=\"foo'",
        "FOO BAR=baz",
        "FOO=bar\\",
        "FOO=\"meow\\\"",
    ];

    const LINES_COMMENTS: [&str; 4] = ["", "   \t  ", "  \t  # something", "#"];

    const LINES_OK: [(&str, (&str, &str)); 5] = [
        ("ID=centos", ("ID", "centos")),
        ("ID='centos'", ("ID", "centos")),
        (
            "NAME='something long \"and weird'",
            ("NAME", "something long \"and weird"),
        ),
        (
            "NAME=\"something long \'and \\\\weird\\\"\\`\"",
            ("NAME", "something long 'and \\weird\"`"),
        ),
        (
            "NAME=unquoted\\\"and\\\\-escaped\\'",
            ("NAME", "unquoted\"and\\-escaped'"),
        ),
    ];

    const CFG_TEXT: &str = "PRETTY_NAME=\"Debian GNU/Linux 11 (bullseye)\"
NAME=\"Debian GNU/Linux\"
VERSION_ID=\"11\"
VERSION=\"11 (bullseye)\"
VERSION_CODENAME=bullseye
ID=debian
HOME_URL=\"https://www.debian.org/\"
SUPPORT_URL=\"https://www.debian.org/support\"
BUG_REPORT_URL=\"https://bugs.debian.org/\"";

    const CFG_EXPECTED: [(&str, Option<&str>); 4] = [
        ("ID", Some("debian")),
        ("VERSION_ID", Some("11")),
        ("VERSION", Some("11 (bullseye)")),
        ("FOO", None),
    ];

    #[test]
    fn parse_bad() {
        let re_line = regex::Regex::new(crate::yai::RE_LINE).unwrap();
        println!("\nMaking sure malformed lines are rejected");
        for line in &LINES_BAD {
            println!("- {:?}", line);
            match crate::yai::parse_line(&re_line, line) {
                Ok(data) => panic!("The {:?} malformed line was misparsed as {:?}", line, data),
                Err(err) => {
                    if !err.downcast_ref::<crate::yai::YAIError>().is_some() {
                        panic!("The {:?} malformed line raised an error: {}", line, err)
                    }
                }
            }
        }
    }

    #[test]
    fn parse_comments() {
        let re_line = regex::Regex::new(crate::yai::RE_LINE).unwrap();
        println!("\nMaking sure comments and empty lines are ignored");
        for line in &LINES_COMMENTS {
            println!("- {:?}", line);
            let res = crate::yai::parse_line(&re_line, line).unwrap();
            println!("  - {:?}", res);
            assert_eq!(res, None);
        }
    }

    #[test]
    fn parse_good() {
        let re_line = regex::Regex::new(crate::yai::RE_LINE).unwrap();
        println!("\nMaking sure well-formed lines are parsed correctly");
        for (line, (varname, value)) in &LINES_OK {
            println!("- {:?}", line);
            let (p_varname, p_value) = crate::yai::parse_line(&re_line, line).unwrap().unwrap();
            println!("  - name {:?} value {:?}", p_varname, p_value);
            assert_eq!(varname, &p_varname);
            assert_eq!(value, &p_value);
        }
    }

    #[test]
    fn parse() -> Result<(), Box<dyn error::Error>> {
        let dir = tempfile::tempdir()?;
        let path = dir.path().join("os-release");
        println!("\nWriting and parsing {}", path.to_string_lossy());
        fs::write(&path, CFG_TEXT.as_bytes())?;
        let res = crate::yai::parse(&path)?;
        assert_eq!(res.len(), 9);
        for (name, value) in &CFG_EXPECTED {
            let pvalue = res.get(&name.to_string());
            println!("- {:?}: expected {:?}, got {:?}", name, value, pvalue);
            match value {
                Some(value) => match pvalue {
                    Some(pvalue) => assert_eq!(value, pvalue),
                    None => panic!("{}: expected {:?} got {:?}", name, value, pvalue),
                },
                None => assert_eq!(pvalue, None),
            }
        }
        Ok(())
    }
}
