-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Dec 03, 2025 at 06:09 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `helpticket_system`
--

-- --------------------------------------------------------

--
-- Table structure for table `attachment`
--

CREATE TABLE `attachment` (
  `id` int(11) NOT NULL,
  `filename` varchar(200) NOT NULL,
  `original_filename` varchar(200) NOT NULL,
  `file_size` int(11) DEFAULT NULL,
  `content_type` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `ticket_id` int(11) NOT NULL,
  `uploaded_by_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `attachment`
--

INSERT INTO `attachment` (`id`, `filename`, `original_filename`, `file_size`, `content_type`, `created_at`, `ticket_id`, `uploaded_by_id`) VALUES
(1, '20251125_090702_17640502514822044052432251189444.jpg', '17640502514822044052432251189444.jpg', 3331517, 'image/jpeg', '2025-11-25 06:07:02', 28, 16);

-- --------------------------------------------------------

--
-- Table structure for table `category`
--

CREATE TABLE `category` (
  `id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `description` varchar(200) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `category`
--

INSERT INTO `category` (`id`, `name`, `description`, `created_at`) VALUES
(1, 'Hardware', 'Computer hardware, printers, peripherals', '2025-06-12 11:37:58'),
(2, 'Software', 'Software installation, updates, licensing', '2025-06-12 11:37:58'),
(3, 'Network', 'Internet connectivity, WiFi, network access', '2025-06-12 11:37:58'),
(4, 'Email', 'Email setup, issues, and configuration', '2025-06-12 11:37:58'),
(5, 'Security', 'Password resets, account access, security concerns', '2025-06-12 11:37:58'),
(6, 'Other', 'General ICT support requests', '2025-06-12 11:37:58'),
(7, 'Voip Maintenance', 'VoIP phones, PBX, and related maintenance', '2025-06-27 05:59:13'),
(8, 'Training', 'ICT-related training requests', '2025-06-27 05:59:14'),
(9, 'University MIS System Issue', 'Issues with university management information systems: AfyaKE, HRMIS, Others', '2025-06-27 05:59:14'),
(10, 'Maintenance ', 'Dusting of computers, cleaning and removal of junk files', '2025-11-24 13:57:12');

-- --------------------------------------------------------

--
-- Table structure for table `comment`
--

CREATE TABLE `comment` (
  `id` int(11) NOT NULL,
  `content` text NOT NULL,
  `is_internal` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `ticket_id` int(11) NOT NULL,
  `author_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `comment`
--

INSERT INTO `comment` (`id`, `content`, `is_internal`, `created_at`, `ticket_id`, `author_id`) VALUES
(1, 'satisfied its working', 0, '2025-11-19 06:01:50', 21, NULL),
(2, 'great\r\n', 1, '2025-11-19 06:03:01', 21, 1),
(3, 'sorted', 0, '2025-11-19 06:05:02', 20, 12),
(4, 'satisfied\r\n', 0, '2025-11-19 14:13:48', 23, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `message`
--

CREATE TABLE `message` (
  `id` int(11) NOT NULL,
  `sender_id` int(11) NOT NULL,
  `receiver_id` int(11) DEFAULT NULL,
  `content` text NOT NULL,
  `timestamp` datetime DEFAULT NULL,
  `ticket_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `message`
--

INSERT INTO `message` (`id`, `sender_id`, `receiver_id`, `content`, `timestamp`, `ticket_id`) VALUES
(1, 1, NULL, 'hello', '2025-06-15 20:21:23', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `notification`
--

CREATE TABLE `notification` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `ticket_id` int(11) DEFAULT NULL,
  `type` varchar(50) NOT NULL,
  `title` varchar(200) NOT NULL,
  `message` text NOT NULL,
  `is_read` tinyint(1) DEFAULT NULL,
  `email_sent` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `read_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `notification`
--

INSERT INTO `notification` (`id`, `user_id`, `ticket_id`, `type`, `title`, `message`, `is_read`, `email_sent`, `created_at`, `read_at`) VALUES
(12, 12, 21, 'ticket_updated', 'Assigned Ticket Updated: #21', 'A ticket assigned to you has been updated by System Administrator.\n\nLocation: SWA - USHR - Hall 13\nStatus: in_progress\nPriority: urgent', 1, 0, '2025-11-18 14:42:10', '2025-11-19 06:05:26'),
(15, 12, 21, 'ticket_closed', 'Assigned Ticket Closed: #21', 'A ticket assigned to you has been closed by System Administrator.\n\nLocation: SWA - USHR - Hall 13', 0, 0, '2025-11-18 14:46:12', NULL),
(16, 12, 20, 'ticket_updated', 'Assigned Ticket Updated: #20', 'A ticket assigned to you has been updated by System Administrator.\n\nLocation: UHS - CMO\nStatus: in_progress\nPriority: urgent', 1, 0, '2025-11-18 14:54:50', '2025-11-19 06:05:37'),
(17, 12, 21, 'new_comment', 'New Comment on Assigned Ticket #21', 'John Shake added a comment to a ticket assigned to you.\n\nLocation: SWA - USHR - Hall 13', 1, 0, '2025-11-19 06:01:50', '2025-11-19 06:05:34'),
(19, 12, 21, 'new_comment', 'New Comment on Assigned Ticket #21', 'System Administrator added a comment to a ticket assigned to you.\n\nLocation: SWA - USHR - Hall 13', 1, 0, '2025-11-19 06:03:01', '2025-11-19 06:05:29'),
(22, 12, 20, 'ticket_closed', 'Assigned Ticket Closed: #20', 'A ticket assigned to you has been closed by System Administrator.\n\nLocation: UHS - CMO', 0, 0, '2025-11-19 06:06:13', NULL),
(25, 12, 22, 'ticket_updated', 'Assigned Ticket Updated: #22', 'A ticket assigned to you has been updated by System Administrator.\n\nLocation: UHS - Staff Clinic\nStatus: in_progress\nPriority: urgent', 0, 0, '2025-11-19 13:48:40', NULL),
(28, 12, 22, 'ticket_closed', 'Assigned Ticket Closed: #22', 'A ticket assigned to you has been closed by System Administrator.\n\nLocation: UHS - Staff Clinic', 0, 0, '2025-11-19 13:53:16', NULL),
(31, 12, 23, 'ticket_updated', 'Assigned Ticket Updated: #23', 'A ticket assigned to you has been updated by System Administrator.\n\nLocation: Confucius - Block B\nStatus: in_progress\nPriority: urgent', 0, 0, '2025-11-19 14:11:50', NULL),
(33, 12, 23, 'ticket_closed', 'Assigned Ticket Closed: #23', 'A ticket assigned to you has been closed by John Shake.\n\nLocation: Confucius - Block B', 0, 0, '2025-11-19 14:13:29', NULL),
(34, 12, 23, 'new_comment', 'New Comment on Assigned Ticket #23', 'John Shake added a comment to a ticket assigned to you.\n\nLocation: Confucius - Block B', 1, 0, '2025-11-19 14:13:49', '2025-11-20 17:16:49'),
(35, 1, 24, 'new_ticket', 'New Unassigned Ticket: #24', 'A new ticket has been created that needs assignment.\n\nLocation: SWA - USHR - Halls Finance\nPriority: medium\nCreated by: Training Intern', 0, 0, '2025-11-24 13:58:45', NULL),
(36, 12, 25, 'ticket_assigned', 'New Ticket Assigned: #25', 'A new ticket has been assigned to you.\n\nLocation: SWA - LSHR - Hall 1\nPriority: urgent\nCreated by: System Administrator', 0, 0, '2025-11-24 14:10:43', NULL),
(37, 1, 26, 'new_ticket', 'New Unassigned Ticket: #26', 'A new ticket has been created that needs assignment.\n\nLocation: Confucius - Block A\nPriority: medium\nCreated by: Training Intern', 0, 0, '2025-11-24 16:15:58', NULL),
(38, 1, NULL, 'new_ticket', 'New Unassigned Ticket: #27', 'A new ticket has been created that needs assignment.\n\nLocation: Confucius - Block A\nPriority: medium\nCreated by: Training Intern', 0, 0, '2025-11-24 16:16:00', NULL),
(39, 1, 28, 'ticket_assigned', 'New Ticket Assigned: #28', 'A new ticket has been assigned to you.\n\nLocation: UHS - Staff Clinic\nPriority: high\nCreated by: Brian Mudola ', 0, 0, '2025-11-25 06:07:02', NULL),
(40, 16, NULL, 'user_registered', 'New User Registration: Kennedy Mwangi', 'A new intern has registered and needs approval.\n\nName: Kennedy Mwangi\nEmail: kennedynduthamw@gmail.com\nUsername: 361393\nRole: Intern\n\nPlease review and approve their account in the user management section.', 0, 0, '2025-11-25 06:12:57', NULL),
(41, 16, NULL, 'user_registered', 'New User Registration: ROTICH ROP ELIAS', 'A new intern has registered and needs approval.\n\nName: ROTICH ROP ELIAS\nEmail: elliespark88@gmail.com\nUsername: 400747\nRole: Intern\n\nPlease review and approve their account in the user management section.', 0, 0, '2025-11-25 08:06:17', NULL),
(42, 16, NULL, 'user_registered', 'New User Registration: Joy Kavulunze', 'A new intern has registered and needs approval.\n\nName: Joy Kavulunze\nEmail: joykavulunze@gmail.com\nUsername: 310805\nRole: Intern\n\nPlease review and approve their account in the user management section.', 0, 0, '2025-11-25 08:06:42', NULL),
(43, 19, NULL, 'account_approved', 'Account Approved - Welcome to ICT Helpdesk!', 'Your account has been approved by Brian Mudola .\n\nYou can now access the ICT Helpdesk system and start working with tickets.\n\nWelcome to the team!', 1, 0, '2025-11-25 08:09:52', '2025-11-28 06:45:23'),
(44, 18, NULL, 'account_approved', 'Account Approved - Welcome to ICT Helpdesk!', 'Your account has been approved by Brian Mudola .\n\nYou can now access the ICT Helpdesk system and start working with tickets.\n\nWelcome to the team!', 1, 0, '2025-11-25 08:09:57', '2025-11-25 09:03:59'),
(45, 17, NULL, 'account_approved', 'Account Approved - Welcome to ICT Helpdesk!', 'Your account has been approved by Brian Mudola .\n\nYou can now access the ICT Helpdesk system and start working with tickets.\n\nWelcome to the team!', 1, 0, '2025-11-25 08:10:02', '2025-11-25 09:17:07'),
(46, 16, NULL, 'user_registered', 'New User Registration: Samwel Ochieng Omondi', 'A new intern has registered and needs approval.\n\nName: Samwel Ochieng Omondi\nEmail: samwelissa124@gmail.com\nUsername: 410133\nRole: Intern\n\nPlease review and approve their account in the user management section.', 0, 0, '2025-11-25 08:14:57', NULL),
(47, 16, NULL, 'new_ticket', 'New Unassigned Ticket: #29', 'A new ticket has been created that needs assignment.\n\nLocation: SWA - LSHR - CCU\nPriority: urgent\nCreated by: Joy Kavulunze', 0, 0, '2025-11-25 08:14:58', NULL),
(48, 21, NULL, 'account_approved', 'Account Approved - Welcome to ICT Helpdesk!', 'Your account has been approved by owido Maurice.\n\nYou can now access the ICT Helpdesk system and start working with tickets.\n\nWelcome to the team!', 0, 0, '2025-11-25 08:21:13', NULL),
(49, 17, 30, 'ticket_assigned', 'New Ticket Assigned: #30', 'A new ticket has been assigned to you.\n\nLocation: Confucius - Block C\nPriority: urgent\nCreated by: Joy Kavulunze', 1, 0, '2025-11-25 11:03:12', '2025-11-27 05:16:51'),
(50, 1, 25, 'ticket_updated', 'Ticket Updated: #25', 'Your ticket has been updated by Training Intern.\n\nLocation: SWA - LSHR - Hall 1\nStatus: resolved\nPriority: urgent', 0, 0, '2025-11-25 15:24:40', NULL),
(51, 1, 31, 'ticket_assigned', 'New Ticket Assigned: #31', 'A new ticket has been assigned to you.\n\nLocation: SWA - USHR - Box Hall 20\nPriority: medium\nCreated by: Training Intern', 0, 0, '2025-11-27 04:46:37', NULL),
(52, 1, 31, 'escalation', 'Escalation: Ticket #31', 'Ticket #31 has been escalated by Training Intern.\n\nLocation: SWA - USHR - Box Hall 20\nPriority: medium\nDescription: Network flacuation', 0, 0, '2025-11-27 04:47:04', NULL),
(53, 16, 31, 'escalation', 'Escalation: Ticket #31', 'Ticket #31 has been escalated by Training Intern.\n\nLocation: SWA - USHR - Box Hall 20\nPriority: medium\nDescription: Network flacuation', 0, 0, '2025-11-27 04:47:05', NULL),
(54, 22, 31, 'escalation', 'Escalation: Ticket #31', 'Ticket #31 has been escalated by Training Intern.\n\nLocation: SWA - USHR - Box Hall 20\nPriority: medium\nDescription: Network flacuation', 0, 0, '2025-11-27 04:47:05', NULL),
(55, 12, 31, 'ticket_updated', 'Ticket Updated: #31', 'Your ticket has been updated by System Administrator.\n\nLocation: SWA - USHR - Box Hall 20\nStatus: in_progress\nPriority: high', 0, 0, '2025-11-27 04:48:47', NULL),
(56, 19, 31, 'ticket_updated', 'Assigned Ticket Updated: #31', 'A ticket assigned to you has been updated by System Administrator.\n\nLocation: SWA - USHR - Box Hall 20\nStatus: in_progress\nPriority: high', 1, 0, '2025-11-27 04:48:47', '2025-11-28 06:45:23'),
(57, 1, 32, 'ticket_assigned', 'New Ticket Assigned: #32', 'A new ticket has been assigned to you.\n\nLocation: SWA - LSHR - Hall 10\nPriority: medium\nCreated by: Kennedy Mwangi', 0, 0, '2025-11-27 04:55:22', NULL),
(58, 1, 31, 'escalation', 'Escalation: Ticket #31', 'Ticket #31 has been escalated by Joy Kavulunze.\n\nLocation: SWA - USHR - Box Hall 20\nPriority: high\nDescription: Network flacuation', 0, 0, '2025-11-27 08:56:43', NULL),
(59, 16, 31, 'escalation', 'Escalation: Ticket #31', 'Ticket #31 has been escalated by Joy Kavulunze.\n\nLocation: SWA - USHR - Box Hall 20\nPriority: high\nDescription: Network flacuation', 0, 0, '2025-11-27 08:56:43', NULL),
(60, 22, 31, 'escalation', 'Escalation: Ticket #31', 'Ticket #31 has been escalated by Joy Kavulunze.\n\nLocation: SWA - USHR - Box Hall 20\nPriority: high\nDescription: Network flacuation', 0, 0, '2025-11-27 08:56:43', NULL),
(61, 1, 35, 'new_ticket', 'New Unassigned Ticket: #35', 'A new ticket has been created that needs assignment.\n\nLocation: SWA - LSHR - CCU\nPriority: medium\nCreated by: Ruth Nambute', 0, 0, '2025-11-28 06:28:47', NULL),
(62, 16, 35, 'new_ticket', 'New Unassigned Ticket: #35', 'A new ticket has been created that needs assignment.\n\nLocation: SWA - LSHR - CCU\nPriority: medium\nCreated by: Ruth Nambute', 0, 0, '2025-11-28 06:28:47', NULL),
(63, 22, 35, 'new_ticket', 'New Unassigned Ticket: #35', 'A new ticket has been created that needs assignment.\n\nLocation: SWA - LSHR - CCU\nPriority: medium\nCreated by: Ruth Nambute', 0, 0, '2025-11-28 06:28:47', NULL),
(64, 24, 35, 'ticket_updated', 'Ticket Updated: #35', 'Your ticket has been updated by Brian Mudola .\n\nLocation: SWA - LSHR - CCU\nStatus: in_progress\nPriority: high', 0, 0, '2025-11-28 06:32:19', NULL),
(65, 18, 35, 'ticket_updated', 'Assigned Ticket Updated: #35', 'A ticket assigned to you has been updated by Brian Mudola .\n\nLocation: SWA - LSHR - CCU\nStatus: in_progress\nPriority: high', 0, 0, '2025-11-28 06:32:20', NULL),
(66, 12, 31, 'ticket_updated', 'Ticket Updated: #31', 'Your ticket has been updated by Joy Kavulunze.\n\nLocation: SWA - USHR - Box Hall 20\nStatus: resolved\nPriority: high', 0, 0, '2025-11-28 06:44:05', NULL),
(67, 1, 36, 'new_ticket', 'New Unassigned Ticket: #36', 'A new ticket has been created that needs assignment.\n\nLocation: UHS - Laboratory\nPriority: medium\nCreated by: Ruth Nambute', 0, 0, '2025-11-28 06:46:21', NULL),
(68, 16, 36, 'new_ticket', 'New Unassigned Ticket: #36', 'A new ticket has been created that needs assignment.\n\nLocation: UHS - Laboratory\nPriority: medium\nCreated by: Ruth Nambute', 0, 0, '2025-11-28 06:46:21', NULL),
(69, 22, 36, 'new_ticket', 'New Unassigned Ticket: #36', 'A new ticket has been created that needs assignment.\n\nLocation: UHS - Laboratory\nPriority: medium\nCreated by: Ruth Nambute', 0, 0, '2025-11-28 06:46:21', NULL),
(70, 24, 36, 'ticket_updated', 'Ticket Updated: #36', 'Your ticket has been updated by Brian Mudola .\n\nLocation: UHS - Laboratory\nStatus: in_progress\nPriority: medium', 0, 0, '2025-11-28 06:47:12', NULL),
(71, 19, 36, 'ticket_updated', 'Assigned Ticket Updated: #36', 'A ticket assigned to you has been updated by Brian Mudola .\n\nLocation: UHS - Laboratory\nStatus: in_progress\nPriority: medium', 0, 0, '2025-11-28 06:47:12', NULL),
(72, 1, NULL, 'user_registered', 'New User Registration: Shake John', 'A new intern has registered and needs approval.\n\nName: Shake John\nEmail: iamshakejohn@gmail.com\nUsername: 030878\nRole: Intern\n\nPlease review and approve their account in the user management section.', 0, 0, '2025-11-28 07:09:13', NULL),
(73, 16, NULL, 'user_registered', 'New User Registration: Shake John', 'A new intern has registered and needs approval.\n\nName: Shake John\nEmail: iamshakejohn@gmail.com\nUsername: 030878\nRole: Intern\n\nPlease review and approve their account in the user management section.', 0, 0, '2025-11-28 07:09:13', NULL),
(74, 22, NULL, 'user_registered', 'New User Registration: Shake John', 'A new intern has registered and needs approval.\n\nName: Shake John\nEmail: iamshakejohn@gmail.com\nUsername: 030878\nRole: Intern\n\nPlease review and approve their account in the user management section.', 0, 0, '2025-11-28 07:09:13', NULL),
(75, 25, NULL, 'account_approved', 'Account Approved - Welcome to ICT Helpdesk!', 'Your account has been approved by Brian Mudola .\n\nYou can now access the ICT Helpdesk system and start working with tickets.\n\nWelcome to the team!', 0, 0, '2025-12-01 16:31:06', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `notification_settings`
--

CREATE TABLE `notification_settings` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `new_ticket_email` tinyint(1) DEFAULT NULL,
  `new_ticket_app` tinyint(1) DEFAULT NULL,
  `ticket_updated_email` tinyint(1) DEFAULT NULL,
  `ticket_updated_app` tinyint(1) DEFAULT NULL,
  `new_comment_email` tinyint(1) DEFAULT NULL,
  `new_comment_app` tinyint(1) DEFAULT NULL,
  `ticket_closed_email` tinyint(1) DEFAULT NULL,
  `ticket_closed_app` tinyint(1) DEFAULT NULL,
  `ticket_overdue_email` tinyint(1) DEFAULT NULL,
  `ticket_overdue_app` tinyint(1) DEFAULT NULL,
  `do_not_disturb` tinyint(1) DEFAULT NULL,
  `dnd_start_time` time DEFAULT NULL,
  `dnd_end_time` time DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `notification_settings`
--

INSERT INTO `notification_settings` (`id`, `user_id`, `new_ticket_email`, `new_ticket_app`, `ticket_updated_email`, `ticket_updated_app`, `new_comment_email`, `new_comment_app`, `ticket_closed_email`, `ticket_closed_app`, `ticket_overdue_email`, `ticket_overdue_app`, `do_not_disturb`, `dnd_start_time`, `dnd_end_time`) VALUES
(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, NULL, NULL),
(3, 12, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, NULL, NULL),
(4, 19, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `report_file`
--

CREATE TABLE `report_file` (
  `id` int(11) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `original_filename` varchar(255) NOT NULL,
  `file_size` int(11) NOT NULL,
  `content_type` varchar(100) NOT NULL,
  `file_category` varchar(50) NOT NULL,
  `description` text DEFAULT NULL,
  `uploaded_by_id` int(11) NOT NULL,
  `uploaded_at` datetime DEFAULT current_timestamp(),
  `department` varchar(100) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `type` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `ticket`
--

CREATE TABLE `ticket` (
  `id` int(11) NOT NULL,
  `location` varchar(200) NOT NULL,
  `description` text NOT NULL,
  `status` varchar(20) NOT NULL,
  `priority` varchar(20) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `closed_at` datetime DEFAULT NULL,
  `created_by_id` int(11) DEFAULT NULL,
  `assigned_to_id` int(11) DEFAULT NULL,
  `category_id` int(11) DEFAULT NULL,
  `closed_by_id` int(11) DEFAULT NULL,
  `due_date` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `ticket`
--

INSERT INTO `ticket` (`id`, `location`, `description`, `status`, `priority`, `created_at`, `updated_at`, `closed_at`, `created_by_id`, `assigned_to_id`, `category_id`, `closed_by_id`, `due_date`) VALUES
(19, 'SWA - LSHR - Hall 2', 'My computer is not working', 'closed', 'medium', '2025-07-27 19:29:48', '2025-11-24 16:29:13', '2025-07-27 16:33:43', NULL, NULL, 1, 1, '2025-07-29 16:32:12'),
(20, 'UHS - CMO', 'My computer is not working', 'closed', 'urgent', '2025-11-18 17:28:42', '2025-11-19 06:06:12', '2025-11-19 06:06:12', 1, NULL, 1, 1, '2025-11-20 14:54:50'),
(21, 'SWA - USHR - Hall 13', 'Network flacuation ', 'closed', 'urgent', '2025-11-18 17:35:03', '2025-11-24 16:16:12', '2025-11-18 14:46:12', NULL, NULL, 3, 1, '2025-11-20 14:42:09'),
(22, 'UHS - Staff Clinic', 'At room 5 i am unable to surf on the internet', 'closed', 'high', '2025-11-19 16:39:05', '2025-11-24 16:16:12', '2025-11-19 13:53:14', NULL, NULL, 3, 1, '2025-11-21 13:48:40'),
(23, 'Confucius - Block B', 'Voip is not working', 'closed', 'urgent', '2025-11-19 17:11:09', '2025-11-24 16:16:12', '2025-11-19 14:13:28', NULL, NULL, 7, NULL, '2025-11-21 14:11:49'),
(24, 'SWA - USHR - Halls Finance', 'Today, we conducted a comprehensive maintenance exercise in the Halls Finance Office. The activities carried out included:\r\n - Dusting and cleaning of CPUs, printers, and keyboards\r\n - Rearranging and organizing cables to enhance tidiness and improve workspace safety\r\n - Cleaning of monitors, CPUs, and keyboards using a foam solution for thorough sanitation\r\nThe exercise ensured a cleaner, more organized, and efficient working environment for the office staffs.', 'open', 'medium', '2025-11-24 16:58:45', '2025-11-24 16:58:45', NULL, 12, NULL, 10, NULL, NULL),
(25, 'SWA - LSHR - Hall 1', 'WiFi isn\'t functioning. thanks check out. and also prioritize check the blindspot areas or any other  cause. ', 'resolved', 'urgent', '2025-11-24 17:10:43', '2025-11-25 15:24:40', NULL, 1, NULL, 3, NULL, NULL),
(26, 'Confucius - Block A', 'Network flacuation', 'open', 'medium', '2025-11-24 19:15:58', '2025-11-24 19:15:58', NULL, 12, NULL, NULL, NULL, NULL),
(28, 'UHS - Staff Clinic', 'At Drug Stores in Dr. Sarah\'s Office. We have installed the new printer brought Laserjet Pro MFP 4103dw.\r\nWe made sure everything is well set. And went further to capture their serial numbers. ', 'open', 'high', '2025-11-25 09:07:02', '2025-11-25 16:19:19', NULL, 16, NULL, 1, NULL, NULL),
(30, 'Confucius - Block C', 'Network Fluctuation over the past two weeks', 'in_progress', 'urgent', '2025-11-25 14:03:12', '2025-11-25 14:03:12', NULL, 19, NULL, 3, NULL, NULL),
(31, 'SWA - USHR - Box Hall 20', 'Network flacuation', 'resolved', 'high', '2025-11-27 07:46:37', '2025-11-28 06:44:05', NULL, 12, NULL, 3, NULL, '2025-11-29 04:48:46'),
(32, 'SWA - LSHR - Hall 10', 'Here is the updated one-paragraph summary:\r\n\r\nHall 10 has been experiencing recurring network fluctuations affecting several Access Points (APs), with the most recent and notable case being the front-center AP on the pole. During a field assessment on Tuesday 25/11/2025, the ICT team discovered that the issue on this AP was caused by a loose cable on the main port. \r\nThe team resolved the problem by reconnecting the cable to the secondary port, which restored normal functionality and stabilized network performance.\r\n', 'in_progress', 'medium', '2025-11-27 07:55:22', '2025-11-27 07:55:22', NULL, 17, NULL, 3, NULL, NULL),
(35, 'SWA - LSHR - CCU', 'hello, can you please come and check up my computer is not working', 'in_progress', 'high', '2025-11-28 09:28:46', '2025-11-28 06:32:19', NULL, 24, NULL, 1, NULL, '2025-11-30 06:32:19'),
(36, 'UHS - Laboratory', 'network issue', 'in_progress', 'medium', '2025-11-28 09:46:20', '2025-11-28 06:47:12', NULL, 24, NULL, 3, NULL, '2025-11-30 06:47:12');

-- --------------------------------------------------------

--
-- Table structure for table `ticket_assignees`
--

CREATE TABLE `ticket_assignees` (
  `ticket_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `ticket_assignees`
--

INSERT INTO `ticket_assignees` (`ticket_id`, `user_id`) VALUES
(20, 12),
(21, 12),
(22, 12),
(23, 12),
(25, 12),
(30, 17),
(31, 19),
(32, 1),
(35, 18),
(36, 19);

-- --------------------------------------------------------

--
-- Table structure for table `ticket_history`
--

CREATE TABLE `ticket_history` (
  `id` int(11) NOT NULL,
  `ticket_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `action` varchar(100) NOT NULL,
  `field_changed` varchar(100) DEFAULT NULL,
  `old_value` varchar(200) DEFAULT NULL,
  `new_value` varchar(200) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `ticket_history`
--

INSERT INTO `ticket_history` (`id`, `ticket_id`, `user_id`, `action`, `field_changed`, `old_value`, `new_value`, `timestamp`) VALUES
(21, 19, 1, 'status changed', 'status', 'open', 'in_progress', '2025-07-27 16:32:12'),
(22, 19, 1, 'reassigned', 'assignees', '[]', '[11]', '2025-07-27 16:32:12'),
(24, 19, 1, 'ticket closed', 'status', 'resolved', 'closed', '2025-07-27 16:33:43'),
(25, 21, 1, 'status changed', 'status', 'open', 'in_progress', '2025-11-18 14:42:09'),
(26, 21, 1, 'reassigned', 'assignees', '[]', '[12]', '2025-11-18 14:42:09'),
(27, 21, 12, 'status changed', 'status', 'in_progress', 'resolved', '2025-11-18 14:45:11'),
(28, 21, 1, 'ticket closed', 'status', 'resolved', 'closed', '2025-11-18 14:46:12'),
(29, 20, 1, 'status changed', 'status', 'open', 'in_progress', '2025-11-18 14:54:50'),
(30, 20, 1, 'priority changed', 'priority', 'medium', 'urgent', '2025-11-18 14:54:50'),
(31, 20, 1, 'reassigned', 'assignees', '[]', '[12]', '2025-11-18 14:54:50'),
(32, 20, 12, 'status changed', 'status', 'in_progress', 'resolved', '2025-11-19 06:04:19'),
(33, 20, 1, 'ticket closed', 'status', 'resolved', 'closed', '2025-11-19 06:06:12'),
(34, 22, 1, 'status changed', 'status', 'open', 'in_progress', '2025-11-19 13:48:40'),
(35, 22, 1, 'priority changed', 'priority', 'medium', 'urgent', '2025-11-19 13:48:40'),
(36, 22, 1, 'reassigned', 'assignees', '[]', '[12]', '2025-11-19 13:48:40'),
(37, 22, 12, 'status changed', 'status', 'in_progress', 'resolved', '2025-11-19 13:50:48'),
(38, 22, 12, 'priority changed', 'priority', 'urgent', 'high', '2025-11-19 13:50:48'),
(39, 22, 1, 'ticket closed', 'status', 'resolved', 'closed', '2025-11-19 13:53:14'),
(40, 23, 1, 'status changed', 'status', 'open', 'in_progress', '2025-11-19 14:11:49'),
(41, 23, 1, 'priority changed', 'priority', 'high', 'urgent', '2025-11-19 14:11:49'),
(42, 23, 1, 'reassigned', 'assignees', '[]', '[12]', '2025-11-19 14:11:49'),
(43, 23, 12, 'status changed', 'status', 'in_progress', 'resolved', '2025-11-19 14:12:37'),
(45, 25, 12, 'status changed', 'status', 'in_progress', 'resolved', '2025-11-25 15:24:40'),
(46, 31, 1, 'priority changed', 'priority', 'medium', 'high', '2025-11-27 04:48:47'),
(47, 31, 1, 'reassigned', 'assignees', '[1]', '[19]', '2025-11-27 04:48:47'),
(48, 35, 16, 'status changed', 'status', 'open', 'in_progress', '2025-11-28 06:32:19'),
(49, 35, 16, 'priority changed', 'priority', 'medium', 'high', '2025-11-28 06:32:19'),
(50, 35, 16, 'reassigned', 'assignees', '[]', '[18]', '2025-11-28 06:32:19'),
(51, 31, 19, 'status changed', 'status', 'in_progress', 'resolved', '2025-11-28 06:44:05'),
(52, 36, 16, 'status changed', 'status', 'open', 'in_progress', '2025-11-28 06:47:12'),
(53, 36, 16, 'reassigned', 'assignees', '[]', '[19]', '2025-11-28 06:47:12');

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE `user` (
  `id` int(11) NOT NULL,
  `username` varchar(64) NOT NULL,
  `email` varchar(120) NOT NULL,
  `password_hash` varchar(256) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `role` varchar(20) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `is_verified` tinyint(1) DEFAULT 0,
  `verification_token` varchar(128) DEFAULT NULL,
  `reset_token` varchar(128) DEFAULT NULL,
  `reset_token_expiry` datetime DEFAULT NULL,
  `phone_number` varchar(20) DEFAULT NULL,
  `is_approved` tinyint(1) DEFAULT 1,
  `approved_by_id` int(11) DEFAULT NULL,
  `approved_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`id`, `username`, `email`, `password_hash`, `full_name`, `role`, `created_at`, `is_active`, `is_verified`, `verification_token`, `reset_token`, `reset_token_expiry`, `phone_number`, `is_approved`, `approved_by_id`, `approved_at`) VALUES
(1, '215030', 'admin@company.com', 'scrypt:32768:8:1$IbakRV0FpBPxvOiH$cae7e78e4640d5e8ee72a085cee12295f74c04b60a27f759a5bbe63c2c9c710838ba98721ca2aa076b20a792655fd6e61ba52f03c7c29f93c1d930d703815142', 'System Administrator', 'admin', '2025-06-12 11:37:58', 1, 0, NULL, NULL, NULL, NULL, 1, NULL, NULL),
(12, 'dctraining', 'intern@company.com', 'scrypt:32768:8:1$Qy8XK7s2Vu43BtOZ$3997a55a257b5eee3a24c3df3120f3800f95e55c7ac9b2e28fb4d3e8663ccaed624df8a965ca9eed01f7359fa3751c2ef1d0bf425eb9d6fa1145b6a9e4b23a38', 'Training Intern', 'intern', '2025-07-28 06:58:32', 1, 1, NULL, NULL, NULL, NULL, 1, NULL, NULL),
(16, '128000', 'kipiamabrian@gmail.com', 'scrypt:32768:8:1$AohfPkSZVqvaLMcs$fd07d3e312fb43a3093e019798f1720255ebc5f70931eb5bce67a65a79adc59f964dfb5266e783d3d6e3c1b7a34dde173fbc47b3a3880c5032474b713b07b8c9', 'Brian Mudola ', 'admin', '2025-11-24 17:03:13', 1, 1, NULL, NULL, NULL, NULL, 1, NULL, NULL),
(17, '361393', 'kennedynduthamw@gmail.com', 'scrypt:32768:8:1$WRR4LOW5D1kfO6Do$9672c127cfec29a81eb5bc3d196b2979df5293dc0d318a003c7da2f9388e4c4aed5c74877967e33ab3ed1f40bbd7bcaa891b737614df58e0f436f57b946b5ef3', 'Kennedy Mwangi', 'intern', '2025-11-25 06:12:57', 1, 1, NULL, NULL, NULL, '+254721494905', 1, 16, '2025-11-25 08:10:02'),
(18, '400747', 'elliespark88@gmail.com', 'scrypt:32768:8:1$biYouzfzUpT0ofnq$090db5ca6ed27c4b115261c906f6a4bfa1058d4e6bddc4be21174aa9a176c5613043c4f7a7263fc00baab31ae4116b1df588c06f47b64180ef9e9c6decc508c5', 'ROTICH ROP ELIAS', 'intern', '2025-11-25 08:06:17', 1, 1, NULL, NULL, NULL, '+254711918556', 1, 16, '2025-11-25 08:09:57'),
(19, '310805', 'joykavulunze@gmail.com', 'scrypt:32768:8:1$geYyez6U2NHd7Kxu$0d885fd6320f640bf052a61300e19edae6adaddb5e56dbb24934f287ba965e798ecb8ad77228fc8a04cc9f78965b1ca4a5caebb2f455860f4f15500bd3a13f8c', 'Joy Kavulunze', 'intern', '2025-11-25 08:06:41', 1, 1, NULL, NULL, NULL, '+254115701158', 1, 16, '2025-11-25 08:09:52'),
(21, '410133', 'samwelissa124@gmail.com', 'scrypt:32768:8:1$ClKCJDRDPDkQUejJ$054033a1f253018517fd614dc0aa34fc467638c3ddf572dbf895e48a98d40fb37570b5666be7a8c485e78f0d73b6d53e470e06a46a1e51cd47ad4ccadf84f2da', 'Samwel Ochieng Omondi', 'intern', '2025-11-25 08:14:57', 1, 1, NULL, NULL, NULL, '+254700392729', 1, 22, '2025-11-25 08:21:13'),
(22, '123456', 'mauriceowido@gmail.com', 'scrypt:32768:8:1$khpZvDd4H2qsG9nb$3d22a872d3c4d6cd9f013cdac0baed53de0ef09ab36ce49680a3bd6743080d8f09df9af61b4d57c2bafcfe8bae21e161569f5fe5bec12ce1b8fac20782236e62', 'owido Maurice', 'admin', '2025-11-25 08:18:28', 1, 1, NULL, NULL, NULL, NULL, 1, NULL, NULL),
(24, '164800', 'ruth.nambute@uonbi.ac.ke', 'scrypt:32768:8:1$f3b08Dy7sD1IjieX$fc410359845c7e93b0ac1b8f7de3484b76b938cd894c712346855c1fac2967b75e075017cb7de637bc1d2c8da2b3b7fa0d2816caa46645b90924f2506cfe2df1', 'Ruth Nambute', 'user', '2025-11-25 15:38:33', 1, 1, NULL, NULL, NULL, '+254765653762', 1, NULL, NULL),
(25, '030878', 'iamshakejohn@gmail.com', 'scrypt:32768:8:1$c7ctMoKNwEakP2q6$9d059d07fc9d43550498d5d0fd39e3592bece4c81f875c5b263e1da9ae6efde8c39e1034346006a5bbafe7119b5eca1a39062e81b236e767e6fdee19aa4dd24c', 'Shake John', 'intern', '2025-11-28 07:09:13', 1, 1, NULL, NULL, NULL, '+254798918206', 1, 16, '2025-12-01 16:31:06');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `attachment`
--
ALTER TABLE `attachment`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ticket_id` (`ticket_id`),
  ADD KEY `uploaded_by_id` (`uploaded_by_id`);

--
-- Indexes for table `category`
--
ALTER TABLE `category`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `comment`
--
ALTER TABLE `comment`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ticket_id` (`ticket_id`),
  ADD KEY `author_id` (`author_id`);

--
-- Indexes for table `message`
--
ALTER TABLE `message`
  ADD PRIMARY KEY (`id`),
  ADD KEY `sender_id` (`sender_id`),
  ADD KEY `receiver_id` (`receiver_id`),
  ADD KEY `ticket_id` (`ticket_id`);

--
-- Indexes for table `notification`
--
ALTER TABLE `notification`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `ticket_id` (`ticket_id`);

--
-- Indexes for table `notification_settings`
--
ALTER TABLE `notification_settings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `report_file`
--
ALTER TABLE `report_file`
  ADD PRIMARY KEY (`id`),
  ADD KEY `uploaded_by_id` (`uploaded_by_id`);

--
-- Indexes for table `ticket`
--
ALTER TABLE `ticket`
  ADD PRIMARY KEY (`id`),
  ADD KEY `created_by_id` (`created_by_id`),
  ADD KEY `assigned_to_id` (`assigned_to_id`),
  ADD KEY `category_id` (`category_id`),
  ADD KEY `fk_ticket_closed_by` (`closed_by_id`);

--
-- Indexes for table `ticket_assignees`
--
ALTER TABLE `ticket_assignees`
  ADD PRIMARY KEY (`ticket_id`,`user_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `ticket_history`
--
ALTER TABLE `ticket_history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ticket_id` (`ticket_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `attachment`
--
ALTER TABLE `attachment`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `category`
--
ALTER TABLE `category`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `comment`
--
ALTER TABLE `comment`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `message`
--
ALTER TABLE `message`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `notification`
--
ALTER TABLE `notification`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=76;

--
-- AUTO_INCREMENT for table `notification_settings`
--
ALTER TABLE `notification_settings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `report_file`
--
ALTER TABLE `report_file`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `ticket`
--
ALTER TABLE `ticket`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=37;

--
-- AUTO_INCREMENT for table `ticket_history`
--
ALTER TABLE `ticket_history`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=54;

--
-- AUTO_INCREMENT for table `user`
--
ALTER TABLE `user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=26;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `attachment`
--
ALTER TABLE `attachment`
  ADD CONSTRAINT `attachment_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `ticket` (`id`),
  ADD CONSTRAINT `attachment_ibfk_2` FOREIGN KEY (`uploaded_by_id`) REFERENCES `user` (`id`);

--
-- Constraints for table `comment`
--
ALTER TABLE `comment`
  ADD CONSTRAINT `comment_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `ticket` (`id`),
  ADD CONSTRAINT `comment_ibfk_2` FOREIGN KEY (`author_id`) REFERENCES `user` (`id`);

--
-- Constraints for table `message`
--
ALTER TABLE `message`
  ADD CONSTRAINT `message_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `user` (`id`),
  ADD CONSTRAINT `message_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `user` (`id`),
  ADD CONSTRAINT `message_ibfk_3` FOREIGN KEY (`ticket_id`) REFERENCES `ticket` (`id`);

--
-- Constraints for table `notification`
--
ALTER TABLE `notification`
  ADD CONSTRAINT `notification_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  ADD CONSTRAINT `notification_ibfk_2` FOREIGN KEY (`ticket_id`) REFERENCES `ticket` (`id`);

--
-- Constraints for table `notification_settings`
--
ALTER TABLE `notification_settings`
  ADD CONSTRAINT `notification_settings_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);

--
-- Constraints for table `report_file`
--
ALTER TABLE `report_file`
  ADD CONSTRAINT `report_file_ibfk_1` FOREIGN KEY (`uploaded_by_id`) REFERENCES `user` (`id`);

--
-- Constraints for table `ticket`
--
ALTER TABLE `ticket`
  ADD CONSTRAINT `fk_ticket_closed_by` FOREIGN KEY (`closed_by_id`) REFERENCES `user` (`id`),
  ADD CONSTRAINT `ticket_ibfk_1` FOREIGN KEY (`created_by_id`) REFERENCES `user` (`id`),
  ADD CONSTRAINT `ticket_ibfk_2` FOREIGN KEY (`assigned_to_id`) REFERENCES `user` (`id`),
  ADD CONSTRAINT `ticket_ibfk_3` FOREIGN KEY (`category_id`) REFERENCES `category` (`id`);

--
-- Constraints for table `ticket_assignees`
--
ALTER TABLE `ticket_assignees`
  ADD CONSTRAINT `ticket_assignees_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `ticket` (`id`),
  ADD CONSTRAINT `ticket_assignees_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);

--
-- Constraints for table `ticket_history`
--
ALTER TABLE `ticket_history`
  ADD CONSTRAINT `ticket_history_ibfk_1` FOREIGN KEY (`ticket_id`) REFERENCES `ticket` (`id`),
  ADD CONSTRAINT `ticket_history_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
