#include "imogenlogger.h"
#include <chrono>
#include <iomanip>
#include <iostream>
#include <errno.h>
#include <sstream>
#include <iostream>


#if defined(_WIN32) || defined(_WIN64)
#include <direct.h>    // For _mkdir, _rmdir
#include <io.h>        // For _unlink
#include <sys/stat.h>  // For _stat
#define stat _stat     // Alias for Windows
#else
#include <sys/stat.h>  // For stat, mkdir
#include <unistd.h>    // For rmdir, unlink
#endif

//Brief impl of some functions in std::filesystem, not available in <C++17
namespace {

    bool exists(const std::string& path) {
        struct stat buffer;
        return (stat(path.c_str(), &buffer) == 0);
    }

    bool create_directory(const std::string& path) {
#if defined(_WIN32) || defined(_WIN64)
        if (_mkdir(path.c_str()) == 0) return true;
        if (errno == EEXIST) return false;
        return false;
#else
        if (mkdir(path.c_str(), 0755) == 0) return true;
        if (errno == EEXIST) return false;
        return false;
#endif
    }

    bool remove(const std::string& path) {
        struct stat buffer;
        if (stat(path.c_str(), &buffer) != 0) return false;

#if defined(_WIN32) || defined(_WIN64)
        if (buffer.st_mode & _S_IFDIR) {
            // Directory
            return (_rmdir(path.c_str()) == 0);
        }
        else {
            // File
            return (_unlink(path.c_str()) == 0);
        }
#else
        if (S_ISDIR(buffer.st_mode)) {
            // Directory
            return (rmdir(path.c_str()) == 0);
        }
        else {
            // File
            return (unlink(path.c_str()) == 0);
        }
#endif
    }

}

// Get singleton instance
ImogenLogger& ImogenLogger::getInstance() {
    static ImogenLogger instance;
    return instance;
}

// Initialize logger
void ImogenLogger::initialize(const std::string& baseDir, LogLevel minLevel) {
    //std::lock_guard<std::mutex> lock(mutex_);
    if (initialized_) {
        logFile_.close();
    }

    // Create logs directory using POSIX mkdir
    std::string logDir = baseDir + "/IMOGEN";
  /*  if (!::create_directory(logDir)) {
        std::cout << "[ERROR] Failed to create log directory: " << logDir << " (errno: " << errno << ")" << std::endl;
        return;
    }*/

    // Generate timestamped filename
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y%m%d_%H%M%S");
    std::string timestamp = ss.str();
    std::string logFilePath = logDir + "/imogen_" + timestamp + ".log";

    // Open log file
    logFile_.open(logFilePath, std::ios::out | std::ios::app);
    if (!logFile_.is_open()) {
        std::cout << "[ERROR] Failed to open log file: " << logFilePath << std::endl;
        return;
    }

    minLevel_ = minLevel;
    initialized_ = true;

    // Log initialization
    log(LogLevel::INFO, "IMOGEN Logger initialized. Log file: " + logFilePath);

}

// Log a message
void ImogenLogger::log(LogLevel level, const std::string& message) {
    if (!initialized_ || level < minLevel_) return;

    ///std::lock_guard<std::mutex> lock(mutex_); //not necessary?
    std::string timestamp = getTimestamp();
    std::string levelStr = levelToString(level);
    std::string logMessage = "[IMOGEN LOGGER][" + timestamp + "] [" + levelStr + "] " + message;

    // Console output (stdout for all levels)
    std::cout << logMessage << std::endl; //use dprintf later?

    // File output
    if (logFile_.is_open()) {
        logFile_ << logMessage << std::endl;
        logFile_.flush();
    }
}

// Set minimum log level
void ImogenLogger::setMinLevel(LogLevel level) {
    //std::lock_guard<std::mutex> lock(mutex_);
    minLevel_ = level;
}

// Destructor
ImogenLogger::~ImogenLogger() {
    //std::lock_guard<std::mutex> lock(mutex_);
    if (logFile_.is_open()) {
        logFile_.close();
    }
}

// Get current timestamp
std::string ImogenLogger::getTimestamp() const {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
    return ss.str();
}

// Convert log level to string
std::string ImogenLogger::levelToString(LogLevel level) const {
    switch (level) {
    case LogLevel::DEBUG: return "DEBUG";
    case LogLevel::INFO:  return "INFO";
    case LogLevel::WARN:  return "WARN";
    case LogLevel::ERROR: return "ERROR";
    default: return "UNKNOWN";
    }
}