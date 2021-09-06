//! Partially-generated data for handling build variants.
//!
//! The [`VariantKind`] enum is meant to be manually kept in sync with
//! the supported StorPool build variants.
//!
//! The full data is provided by the external ``variants-all.json`` file in
//! the StorPool source tree.

use std::str::FromStr;

use serde::{Deserialize, Serialize};

use crate::VariantError;

/// The supported StorPool build variants (OS distribution, version, etc).
#[derive(Debug, Clone, PartialEq, Hash, Eq, Serialize, Deserialize)]
pub enum VariantKind {
    /// AlmaLinux 8.x
    ALMA8,
    /// CentOS 6.x
    CENTOS6,
    /// CentOS 7.x
    CENTOS7,
    /// CentOS 8.x
    CENTOS8,
    /// Oracle Linux 7.x
    ORACLE7,
    /// Debian 9.x (stretch)
    DEBIAN9,
    /// Debian 10.x (buster)
    DEBIAN10,
    /// Debian 11.x (bullseye)
    DEBIAN11,
    /// Debian 12.x (bookworm)
    DEBIAN12,
    /// RedHat Enterprise Linux 8.x
    RHEL8,
    /// Rocky Linux 8.x
    ROCKY8,
    /// Ubuntu 16.04 LTS (Xenial Xerus)
    UBUNTU1604,
    /// Ubuntu 18.04 LTS (Bionic Beaver)
    UBUNTU1804,
    /// Ubuntu 20.04 LTS (Focal Fossa)
    UBUNTU2004,
}

impl VariantKind {
    const ALMA8_NAME: &'static str = "ALMA8";
    const CENTOS6_NAME: &'static str = "CENTOS6";
    const CENTOS7_NAME: &'static str = "CENTOS7";
    const CENTOS8_NAME: &'static str = "CENTOS8";
    const ORACLE7_NAME: &'static str = "ORACLE7";
    const DEBIAN9_NAME: &'static str = "DEBIAN9";
    const DEBIAN10_NAME: &'static str = "DEBIAN10";
    const DEBIAN11_NAME: &'static str = "DEBIAN11";
    const DEBIAN12_NAME: &'static str = "DEBIAN12";
    const RHEL8_NAME: &'static str = "RHEL8";
    const ROCKY8_NAME: &'static str = "ROCKY8";
    const UBUNTU1604_NAME: &'static str = "UBUNTU1604";
    const UBUNTU1804_NAME: &'static str = "UBUNTU1804";
    const UBUNTU2004_NAME: &'static str = "UBUNTU2004";
}

impl AsRef<str> for VariantKind {
    fn as_ref(&self) -> &str {
        match self {
            VariantKind::ALMA8 => VariantKind::ALMA8_NAME,
            VariantKind::CENTOS6 => VariantKind::CENTOS6_NAME,
            VariantKind::CENTOS7 => VariantKind::CENTOS7_NAME,
            VariantKind::CENTOS8 => VariantKind::CENTOS8_NAME,
            VariantKind::ORACLE7 => VariantKind::ORACLE7_NAME,
            VariantKind::DEBIAN9 => VariantKind::DEBIAN9_NAME,
            VariantKind::DEBIAN10 => VariantKind::DEBIAN10_NAME,
            VariantKind::DEBIAN11 => VariantKind::DEBIAN11_NAME,
            VariantKind::DEBIAN12 => VariantKind::DEBIAN12_NAME,
            VariantKind::RHEL8 => VariantKind::RHEL8_NAME,
            VariantKind::ROCKY8 => VariantKind::ROCKY8_NAME,
            VariantKind::UBUNTU1604 => VariantKind::UBUNTU1604_NAME,
            VariantKind::UBUNTU1804 => VariantKind::UBUNTU1804_NAME,
            VariantKind::UBUNTU2004 => VariantKind::UBUNTU2004_NAME,
        }
    }
}

impl FromStr for VariantKind {
    type Err = VariantError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            VariantKind::ALMA8_NAME => Ok(VariantKind::ALMA8),
            VariantKind::CENTOS6_NAME => Ok(VariantKind::CENTOS6),
            VariantKind::CENTOS7_NAME => Ok(VariantKind::CENTOS7),
            VariantKind::CENTOS8_NAME => Ok(VariantKind::CENTOS8),
            VariantKind::ORACLE7_NAME => Ok(VariantKind::ORACLE7),
            VariantKind::DEBIAN9_NAME => Ok(VariantKind::DEBIAN9),
            VariantKind::DEBIAN10_NAME => Ok(VariantKind::DEBIAN10),
            VariantKind::DEBIAN11_NAME => Ok(VariantKind::DEBIAN11),
            VariantKind::DEBIAN12_NAME => Ok(VariantKind::DEBIAN12),
            VariantKind::RHEL8_NAME => Ok(VariantKind::RHEL8),
            VariantKind::ROCKY8_NAME => Ok(VariantKind::ROCKY8),
            VariantKind::UBUNTU1604_NAME => Ok(VariantKind::UBUNTU1604),
            VariantKind::UBUNTU1804_NAME => Ok(VariantKind::UBUNTU1804),
            VariantKind::UBUNTU2004_NAME => Ok(VariantKind::UBUNTU2004),
            other => Err(VariantError::BadVariant(other.to_string())),
        }
    }
}

/// Return the JSON definition of the StorPool variants.
pub fn get_json_def() -> Vec<u8> {
    include_bytes!("variants-all.json").to_vec()
}
