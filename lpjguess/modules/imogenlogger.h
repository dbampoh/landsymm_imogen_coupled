#pragma once
#ifndef IMOGEN_LOGGER_H
#define IMOGEN_LOGGER_H

#include <string>
#include <fstream>
#include "parameters.h" //for IMOGENConfig

// Logger class for IMOGEN
class ImogenLogger {
public:
    // Log levels
    enum class LogLevel { DEBUG, INFO, WARN, ERROR };

    // Singleton instance
    static ImogenLogger& getInstance();

    // Initialize logger with base directory and optional minimum log level
    void initialize(const std::string& baseDir = (char*)IMOGENConfig::DIR_COMMON,
        LogLevel minLevel = LogLevel::INFO);

    // Log a message with specified level
    void log(LogLevel level, const std::string& message);

    // Convenience methods for each log level
    void debug(const std::string& message) { log(LogLevel::DEBUG, message); }
    void info(const std::string& message) { log(LogLevel::INFO, message); }
    void warn(const std::string& message) { log(LogLevel::WARN, message); }
    void error(const std::string& message) { log(LogLevel::ERROR, message); }

    // Set minimum log level
    void setMinLevel(LogLevel level);

private:
    ImogenLogger() = default;
    ~ImogenLogger();

    // Prevent copying
    ImogenLogger(const ImogenLogger&) = delete;
    ImogenLogger& operator=(const ImogenLogger&) = delete;

    // Helper methods
    std::string getTimestamp() const;
    std::string levelToString(LogLevel level) const;

    std::ofstream logFile_;
    //std::mutex mutex_;
    LogLevel minLevel_ = LogLevel::INFO;
    bool initialized_ = false;
};

#endif // IMOGEN_LOGGER_H