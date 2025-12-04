use std::io;

#[derive(Debug, Clone, PartialEq)]
pub enum ParseError {
    InsufficientData,
    IoError(String),
    InvalidData(String),
}

impl From<io::Error> for ParseError {
    fn from(error: io::Error) -> Self {
        ParseError::IoError(error.to_string())
    }
}

impl std::fmt::Display for ParseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ParseError::InsufficientData => write!(f, "Insufficient data for parsing"),
            ParseError::IoError(msg) => write!(f, "IO error: {}", msg),
            ParseError::InvalidData(msg) => write!(f, "Invalid data: {}", msg),
        }
    }
}

impl std::error::Error for ParseError {}
