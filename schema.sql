-- Exam Proctoring System Database Schema
-- Compatible with MySQL 5.7+ and MySQL 8.0+

CREATE DATABASE IF NOT EXISTS `exam_proctoring`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `exam_proctoring`;

-- 1. Teachers Table
CREATE TABLE IF NOT EXISTS `teachers` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `subject` VARCHAR(100) NOT NULL,
    `department` VARCHAR(100) DEFAULT '',
    `password` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Students Table
CREATE TABLE IF NOT EXISTS `students` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `roll_no` VARCHAR(50) NOT NULL UNIQUE,
    `department` VARCHAR(100) DEFAULT '',
    `class` VARCHAR(50) DEFAULT '',
    `password` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Exams Questions Table
CREATE TABLE IF NOT EXISTS `exams` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `teacher_name` VARCHAR(100) NOT NULL,
    `subject` VARCHAR(100) NOT NULL,
    `question` TEXT NOT NULL,
    `option1` TEXT NOT NULL,
    `option2` TEXT NOT NULL,
    `option3` TEXT NOT NULL,
    `option4` TEXT NOT NULL,
    `answer` TEXT NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_subject` (`subject`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Exam Results Table
CREATE TABLE IF NOT EXISTS `results` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `student_name` VARCHAR(100) NOT NULL,
    `roll_no` VARCHAR(50) NOT NULL,
    `teacher_name` VARCHAR(100) NOT NULL,
    `subject` VARCHAR(100) NOT NULL,
    `department` VARCHAR(100) DEFAULT '',
    `score` INT DEFAULT 0,
    `warnings` INT DEFAULT 0,
    `mobile_warnings` INT DEFAULT 0,
    `eye_warnings` INT DEFAULT 0,
    `tab_warnings` INT DEFAULT 0,
    `face_warnings` INT DEFAULT 0,
    `submitted_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_subject` (`subject`),
    INDEX `idx_roll_no` (`roll_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
