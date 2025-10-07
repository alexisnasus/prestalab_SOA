-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Host: db
-- Generation Time: Oct 07, 2025 at 12:20 PM
-- Server version: 8.0.43
-- PHP Version: 8.2.27

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `soa_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `atraso`
--

CREATE TABLE `atraso` (
  `id` bigint NOT NULL,
  `prestamo_id` bigint NOT NULL,
  `dias_atraso` int NOT NULL,
  `estado` varchar(20) NOT NULL,
  `registro_instante` datetime NOT NULL
) ;

-- --------------------------------------------------------

--
-- Table structure for table `configuracion_sistema`
--

CREATE TABLE `configuracion_sistema` (
  `id` bigint NOT NULL,
  `clave` varchar(50) NOT NULL,
  `valor` varchar(100) NOT NULL,
  `descripcion` text,
  `registro_instante` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `item`
--

CREATE TABLE `item` (
  `id` bigint NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `cantidad` int NOT NULL,
  `tipo` varchar(20) NOT NULL,
  `valor` decimal(10,2) NOT NULL,
  `tarifa_atraso` decimal(10,2) NOT NULL,
  `descripcion` varchar(100) NOT NULL,
  `cantidad_max` int NOT NULL,
  `registro_instante` datetime NOT NULL
) ;

--
-- Dumping data for table `item`
--

INSERT INTO `item` (`id`, `nombre`, `cantidad`, `tipo`, `valor`, `tarifa_atraso`, `descripcion`, `cantidad_max`, `registro_instante`) VALUES
(1, 'Raspberry Pi 4', 50, 'EQUIPO_ELECTRONICO', 64990.00, 500.00, 'Broadcom BCM2711, quad-core Cortex-A72 (ARM v8) SoC de 64 bits @ 1. 5 GHz2', 1, '2025-09-29 17:30:40'),
(2, 'Lenovo ThinkPad X1', 20, 'EQUIPO_ELECTRONICO', 1839000.00, 500.00, 'Intel Ultra 7 258V (Beats U7 165), 14\" 2.8K (2880 x 1800)', 1, '2025-09-29 17:39:40'),
(3, 'TP-Link AX1800', 40, 'EQUIPO_ELECTRONICO', 52990.00, 500.00, 'WiFi 6 Router V4 (Archer AX21)', 1, '2025-09-29 17:41:48'),
(4, 'Arduino Uno R4', 100, 'EQUIPO_ELECTRONICO', 24990.00, 500.00, 'Microcontrolador ATmega4809 con conectividad USB-C', 2, '2025-09-29 18:00:00'),
(5, 'Samsung Galaxy Tab S9', 15, 'EQUIPO_ELECTRONICO', 899990.00, 500.00, 'Pantalla AMOLED 11\" con Snapdragon 8 Gen 2', 1, '2025-09-29 18:05:00'),
(6, 'Canon EOS R50', 10, 'EQUIPO_ELECTRONICO', 849990.00, 500.00, 'Cámara mirrorless APS-C con grabación 4K 30fps', 1, '2025-09-29 18:10:00'),
(7, 'Logitech MX Master 3S', 60, 'EQUIPO_ELECTRONICO', 89990.00, 500.00, 'Mouse inalámbrico avanzado con carga USB-C', 2, '2025-09-29 18:15:00'),
(8, 'Kindle Paperwhite 2023', 30, 'EQUIPO_ELECTRONICO', 139990.00, 500.00, 'Pantalla de 6.8\" con luz cálida ajustable', 1, '2025-09-29 18:20:00');

-- --------------------------------------------------------

--
-- Table structure for table `item_existencia`
--

CREATE TABLE `item_existencia` (
  `id` bigint NOT NULL,
  `item_id` bigint NOT NULL,
  `sede_id` bigint NOT NULL,
  `codigo` varchar(50) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `registro_instante` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `item_existencia`
--

INSERT INTO `item_existencia` (`id`, `item_id`, `sede_id`, `codigo`, `estado`, `registro_instante`) VALUES
(1, 1, 1, '001001001', 'DISPONIBLE', '2025-09-30 10:00:00'),
(2, 1, 1, '001001002', 'DISPONIBLE', '2025-09-30 10:01:00'),
(3, 1, 1, '001001003', 'DISPONIBLE', '2025-09-30 10:02:00'),
(4, 1, 1, '001001004', 'DISPONIBLE', '2025-09-30 10:03:00'),
(5, 1, 1, '001001005', 'DISPONIBLE', '2025-09-30 10:04:00'),
(6, 2, 1, '001002001', 'DISPONIBLE', '2025-09-30 10:05:00'),
(7, 2, 1, '001002002', 'DISPONIBLE', '2025-09-30 10:06:00'),
(8, 2, 1, '001002003', 'DISPONIBLE', '2025-09-30 10:07:00'),
(9, 2, 1, '001002004', 'DISPONIBLE', '2025-09-30 10:08:00'),
(10, 2, 1, '001002005', 'DISPONIBLE', '2025-09-30 10:09:00'),
(11, 3, 1, '001003001', 'DISPONIBLE', '2025-09-30 10:10:00'),
(12, 3, 1, '001003002', 'DISPONIBLE', '2025-09-30 10:11:00'),
(13, 3, 1, '001003003', 'DISPONIBLE', '2025-09-30 10:12:00'),
(14, 3, 1, '001003004', 'DISPONIBLE', '2025-09-30 10:13:00'),
(15, 3, 1, '001003005', 'DISPONIBLE', '2025-09-30 10:14:00'),
(16, 4, 1, '001004001', 'PRESTADO', '2025-09-30 10:15:00'),
(17, 4, 1, '001004002', 'DISPONIBLE', '2025-09-30 10:16:00'),
(18, 4, 1, '001004003', 'DISPONIBLE', '2025-09-30 10:17:00'),
(19, 4, 1, '001004004', 'DISPONIBLE', '2025-09-30 10:18:00'),
(20, 4, 1, '001004005', 'DISPONIBLE', '2025-09-30 10:19:00'),
(21, 5, 1, '001005001', 'DISPONIBLE', '2025-09-30 10:20:00'),
(22, 5, 1, '001005002', 'DISPONIBLE', '2025-09-30 10:21:00'),
(23, 5, 1, '001005003', 'DISPONIBLE', '2025-09-30 10:22:00'),
(24, 5, 1, '001005004', 'DISPONIBLE', '2025-09-30 10:23:00'),
(25, 5, 1, '001005005', 'DISPONIBLE', '2025-09-30 10:24:00'),
(26, 6, 1, '001006001', 'DISPONIBLE', '2025-09-30 10:25:00'),
(27, 6, 1, '001006002', 'DISPONIBLE', '2025-09-30 10:26:00'),
(28, 6, 1, '001006003', 'DISPONIBLE', '2025-09-30 10:27:00'),
(29, 6, 1, '001006004', 'DISPONIBLE', '2025-09-30 10:28:00'),
(30, 6, 1, '001006005', 'DISPONIBLE', '2025-09-30 10:29:00'),
(31, 7, 1, '001007001', 'DISPONIBLE', '2025-09-30 10:30:00'),
(32, 7, 1, '001007002', 'DISPONIBLE', '2025-09-30 10:31:00'),
(33, 7, 1, '001007003', 'DISPONIBLE', '2025-09-30 10:32:00'),
(34, 7, 1, '001007004', 'DISPONIBLE', '2025-09-30 10:33:00'),
(35, 7, 1, '001007005', 'DISPONIBLE', '2025-09-30 10:34:00'),
(36, 8, 1, '001008001', 'DISPONIBLE', '2025-09-30 10:35:00'),
(37, 8, 1, '001008002', 'DISPONIBLE', '2025-09-30 10:36:00'),
(38, 8, 1, '001008003', 'DISPONIBLE', '2025-09-30 10:37:00'),
(39, 8, 1, '001008004', 'DISPONIBLE', '2025-09-30 10:38:00'),
(40, 8, 1, '001008005', 'DISPONIBLE', '2025-09-30 10:39:00'),
(41, 1, 2, '002001001', 'DISPONIBLE', '2025-09-30 10:40:00'),
(42, 1, 2, '002001002', 'DISPONIBLE', '2025-09-30 10:41:00'),
(43, 1, 2, '002001003', 'DISPONIBLE', '2025-09-30 10:42:00'),
(44, 1, 2, '002001004', 'DISPONIBLE', '2025-09-30 10:43:00'),
(45, 1, 2, '002001005', 'DISPONIBLE', '2025-09-30 10:44:00'),
(46, 2, 2, '002002001', 'DISPONIBLE', '2025-09-30 10:45:00'),
(47, 2, 2, '002002002', 'DISPONIBLE', '2025-09-30 10:46:00'),
(48, 2, 2, '002002003', 'DISPONIBLE', '2025-09-30 10:47:00'),
(49, 2, 2, '002002004', 'DISPONIBLE', '2025-09-30 10:48:00'),
(50, 2, 2, '002002005', 'DISPONIBLE', '2025-09-30 10:49:00'),
(51, 3, 2, '002003001', 'DISPONIBLE', '2025-09-30 10:50:00'),
(52, 3, 2, '002003002', 'DISPONIBLE', '2025-09-30 10:51:00'),
(53, 3, 2, '002003003', 'DISPONIBLE', '2025-09-30 10:52:00'),
(54, 3, 2, '002003004', 'DISPONIBLE', '2025-09-30 10:53:00'),
(55, 3, 2, '002003005', 'DISPONIBLE', '2025-09-30 10:54:00'),
(56, 4, 2, '002004001', 'DISPONIBLE', '2025-09-30 10:55:00'),
(57, 4, 2, '002004002', 'DISPONIBLE', '2025-09-30 10:56:00'),
(58, 4, 2, '002004003', 'DISPONIBLE', '2025-09-30 10:57:00'),
(59, 4, 2, '002004004', 'DISPONIBLE', '2025-09-30 10:58:00'),
(60, 4, 2, '002004005', 'DISPONIBLE', '2025-09-30 10:59:00'),
(61, 5, 2, '002005001', 'DISPONIBLE', '2025-09-30 11:00:00'),
(62, 5, 2, '002005002', 'DISPONIBLE', '2025-09-30 11:01:00'),
(63, 5, 2, '002005003', 'DISPONIBLE', '2025-09-30 11:02:00'),
(64, 5, 2, '002005004', 'DISPONIBLE', '2025-09-30 11:03:00'),
(65, 5, 2, '002005005', 'DISPONIBLE', '2025-09-30 11:04:00'),
(66, 6, 2, '002006001', 'DISPONIBLE', '2025-09-30 11:05:00'),
(67, 6, 2, '002006002', 'DISPONIBLE', '2025-09-30 11:06:00'),
(68, 6, 2, '002006003', 'DISPONIBLE', '2025-09-30 11:07:00'),
(69, 6, 2, '002006004', 'DISPONIBLE', '2025-09-30 11:08:00'),
(70, 6, 2, '002006005', 'DISPONIBLE', '2025-09-30 11:09:00'),
(71, 7, 2, '002007001', 'DISPONIBLE', '2025-09-30 11:10:00'),
(72, 7, 2, '002007002', 'DISPONIBLE', '2025-09-30 11:11:00'),
(73, 7, 2, '002007003', 'DISPONIBLE', '2025-09-30 11:12:00'),
(74, 7, 2, '002007004', 'DISPONIBLE', '2025-09-30 11:13:00'),
(75, 7, 2, '002007005', 'DISPONIBLE', '2025-09-30 11:14:00'),
(76, 8, 2, '002008001', 'DISPONIBLE', '2025-09-30 11:15:00'),
(77, 8, 2, '002008002', 'DISPONIBLE', '2025-09-30 11:16:00'),
(78, 8, 2, '002008003', 'DISPONIBLE', '2025-09-30 11:17:00'),
(79, 8, 2, '002008004', 'DISPONIBLE', '2025-09-30 11:18:00'),
(80, 8, 2, '002008005', 'DISPONIBLE', '2025-09-30 11:19:00'),
(81, 1, 3, '003001001', 'DISPONIBLE', '2025-09-30 11:20:00'),
(82, 1, 3, '003001002', 'DISPONIBLE', '2025-09-30 11:21:00'),
(83, 1, 3, '003001003', 'DISPONIBLE', '2025-09-30 11:22:00'),
(84, 1, 3, '003001004', 'DISPONIBLE', '2025-09-30 11:23:00'),
(85, 1, 3, '003001005', 'DISPONIBLE', '2025-09-30 11:24:00'),
(86, 2, 3, '003002001', 'DISPONIBLE', '2025-09-30 11:25:00'),
(87, 2, 3, '003002002', 'DISPONIBLE', '2025-09-30 11:26:00'),
(88, 2, 3, '003002003', 'DISPONIBLE', '2025-09-30 11:27:00'),
(89, 2, 3, '003002004', 'DISPONIBLE', '2025-09-30 11:28:00'),
(90, 2, 3, '003002005', 'DISPONIBLE', '2025-09-30 11:29:00'),
(91, 3, 3, '003003001', 'DISPONIBLE', '2025-09-30 11:30:00'),
(92, 3, 3, '003003002', 'DISPONIBLE', '2025-09-30 11:31:00'),
(93, 3, 3, '003003003', 'DISPONIBLE', '2025-09-30 11:32:00'),
(94, 3, 3, '003003004', 'DISPONIBLE', '2025-09-30 11:33:00'),
(95, 3, 3, '003003005', 'DISPONIBLE', '2025-09-30 11:34:00'),
(96, 4, 3, '003004001', 'DISPONIBLE', '2025-09-30 11:35:00'),
(97, 4, 3, '003004002', 'DISPONIBLE', '2025-09-30 11:36:00'),
(98, 4, 3, '003004003', 'DISPONIBLE', '2025-09-30 11:37:00'),
(99, 4, 3, '003004004', 'DISPONIBLE', '2025-09-30 11:38:00'),
(100, 4, 3, '003004005', 'DISPONIBLE', '2025-09-30 11:39:00'),
(101, 5, 3, '003005001', 'DISPONIBLE', '2025-09-30 11:40:00'),
(102, 5, 3, '003005002', 'DISPONIBLE', '2025-09-30 11:41:00'),
(103, 5, 3, '003005003', 'DISPONIBLE', '2025-09-30 11:42:00'),
(104, 5, 3, '003005004', 'DISPONIBLE', '2025-09-30 11:43:00'),
(105, 5, 3, '003005005', 'DISPONIBLE', '2025-09-30 11:44:00'),
(106, 6, 3, '003006001', 'DISPONIBLE', '2025-09-30 11:45:00'),
(107, 6, 3, '003006002', 'DISPONIBLE', '2025-09-30 11:46:00'),
(108, 6, 3, '003006003', 'DISPONIBLE', '2025-09-30 11:47:00'),
(109, 6, 3, '003006004', 'DISPONIBLE', '2025-09-30 11:48:00'),
(110, 6, 3, '003006005', 'DISPONIBLE', '2025-09-30 11:49:00'),
(111, 7, 3, '003007001', 'DISPONIBLE', '2025-09-30 11:50:00'),
(112, 7, 3, '003007002', 'DISPONIBLE', '2025-09-30 11:51:00'),
(113, 7, 3, '003007003', 'DISPONIBLE', '2025-09-30 11:52:00'),
(114, 7, 3, '003007004', 'DISPONIBLE', '2025-09-30 11:53:00'),
(115, 7, 3, '003007005', 'DISPONIBLE', '2025-09-30 11:53:00'),
(116, 8, 3, '003008001', 'DISPONIBLE', '2025-09-30 11:54:00'),
(117, 8, 3, '003008002', 'DISPONIBLE', '2025-09-30 11:55:00'),
(118, 8, 3, '003008003', 'DISPONIBLE', '2025-09-30 11:56:00'),
(119, 8, 3, '003008004', 'DISPONIBLE', '2025-09-30 11:57:00'),
(120, 8, 3, '003008005', 'DISPONIBLE', '2025-09-30 11:58:00');

-- --------------------------------------------------------

--
-- Table structure for table `item_solicitud`
--

CREATE TABLE `item_solicitud` (
  `solicitud_id` bigint NOT NULL,
  `item_id` bigint NOT NULL,
  `cantidad` int NOT NULL,
  `registro_instante` datetime NOT NULL
) ;

--
-- Dumping data for table `item_solicitud`
--

INSERT INTO `item_solicitud` (`solicitud_id`, `item_id`, `cantidad`, `registro_instante`) VALUES
(1, 2, 1, '2025-09-29 17:43:17'),
(2, 3, 2, '2025-09-29 17:51:38'),
(3, 4, 1, '2025-09-29 18:02:00'),
(4, 1, 2, '2025-09-29 18:06:00'),
(5, 7, 1, '2025-09-29 18:11:00'),
(6, 2, 1, '2025-09-29 18:16:00'),
(7, 5, 2, '2025-09-29 18:21:00'),
(8, 3, 1, '2025-09-29 18:26:00'),
(9, 8, 2, '2025-09-29 18:31:00');

-- --------------------------------------------------------

--
-- Table structure for table `lista_espera`
--

CREATE TABLE `lista_espera` (
  `id` bigint NOT NULL,
  `solicitud_id` bigint NOT NULL,
  `item_id` bigint NOT NULL,
  `fecha_ingreso` datetime NOT NULL,
  `estado` varchar(20) NOT NULL,
  `registro_instante` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `multa`
--

CREATE TABLE `multa` (
  `id` bigint NOT NULL,
  `prestamo_id` bigint NOT NULL,
  `motivo` varchar(20) NOT NULL,
  `valor` decimal(10,2) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `registro_instante` datetime NOT NULL
) ;

-- --------------------------------------------------------

--
-- Table structure for table `notificacion`
--

CREATE TABLE `notificacion` (
  `id` bigint NOT NULL,
  `usuario_id` bigint NOT NULL,
  `canal` int NOT NULL,
  `tipo` varchar(20) NOT NULL,
  `mensaje` text NOT NULL,
  `registro_instante` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `notificacion`
--

INSERT INTO `notificacion` (`id`, `usuario_id`, `canal`, `tipo`, `mensaje`, `registro_instante`) VALUES
(1, 197407514, 1, 'RECORDATORIO', 'Recuerda que el sol se esconde por la costa. Mientras que al amanecer sale por la cordillera.', '2025-09-29 17:27:31');

-- --------------------------------------------------------

--
-- Table structure for table `prestamo`
--

CREATE TABLE `prestamo` (
  `id` bigint NOT NULL,
  `item_existencia_id` bigint NOT NULL,
  `solicitud_id` bigint NOT NULL,
  `fecha_prestamo` datetime NOT NULL,
  `fecha_devolucion` datetime DEFAULT NULL,
  `comentario` text,
  `estado` varchar(20) NOT NULL,
  `renovaciones_realizadas` int NOT NULL DEFAULT '0',
  `registro_instante` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `prestamo`
--

INSERT INTO `prestamo` (`id`, `item_existencia_id`, `solicitud_id`, `fecha_prestamo`, `fecha_devolucion`, `comentario`, `estado`, `renovaciones_realizadas`, `registro_instante`) VALUES
(1, 16, 3, '2025-09-30 16:40:07', '2025-10-30 13:40:07', NULL, 'ACTIVO', 0, '2025-09-30 16:40:07');

-- --------------------------------------------------------

--
-- Table structure for table `sede`
--

CREATE TABLE `sede` (
  `id` bigint NOT NULL,
  `nombre` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `sede`
--

INSERT INTO `sede` (`id`, `nombre`) VALUES
(1, 'FIC_LABORATORIO_01'),
(2, 'FIC_LABORATORIO_02'),
(3, 'FIC_LABORATORIO_03');

-- --------------------------------------------------------

--
-- Table structure for table `solicitud`
--

CREATE TABLE `solicitud` (
  `id` bigint NOT NULL,
  `usuario_id` bigint NOT NULL,
  `tipo` varchar(30) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `registro_instante` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `solicitud`
--

INSERT INTO `solicitud` (`id`, `usuario_id`, `tipo`, `estado`, `registro_instante`) VALUES
(1, 197407514, 'PRÉSTAMO', 'PENDIENTE', '2025-09-29 17:20:59'),
(2, 197407514, 'PRÉSTAMO', 'RECHAZADA', '2025-09-29 17:49:29'),
(3, 204587321, 'PRÉSTAMO', 'APROBADA', '2025-09-29 18:00:00'),
(4, 189453276, 'PRÉSTAMO', 'RECHAZADA', '2025-09-29 18:05:00'),
(5, 174892345, 'RENOVACIÓN', 'PENDIENTE', '2025-09-29 18:10:00'),
(6, 165982311, 'PRÉSTAMO', 'APROBADA', '2025-09-29 18:15:00'),
(7, 152398765, 'VENTANA', 'PENDIENTE', '2025-09-29 18:20:00'),
(8, 197407514, 'RENOVACIÓN', 'APROBADA', '2025-09-29 18:25:00'),
(9, 140987654, 'VENTANA', 'APROBADA', '2025-09-29 18:30:00');

-- --------------------------------------------------------

--
-- Table structure for table `sugerencia`
--

CREATE TABLE `sugerencia` (
  `id` bigint NOT NULL,
  `usuario_id` bigint NOT NULL,
  `sugerencia` varchar(100) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `registro_instante` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `sugerencia`
--

INSERT INTO `sugerencia` (`id`, `usuario_id`, `sugerencia`, `estado`, `registro_instante`) VALUES
(1, 197407514, 'Un frontend sería muy útil', 'RECHAZADA', '2025-09-29 17:23:57'),
(2, 197407514, 'Un buen framework de front podría ser NextJS (React)', 'PENDIENTE', '2025-09-30 15:42:36');

-- --------------------------------------------------------

--
-- Table structure for table `usuario`
--

CREATE TABLE `usuario` (
  `id` bigint NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `correo` varchar(50) NOT NULL,
  `tipo` varchar(20) NOT NULL,
  `telefono` varchar(15) NOT NULL,
  `estado` varchar(20) NOT NULL,
  `preferencias_notificacion` int NOT NULL DEFAULT '0',
  `registro_instante` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `usuario`
--

INSERT INTO `usuario` (`id`, `nombre`, `correo`, `tipo`, `telefono`, `estado`, `preferencias_notificacion`, `registro_instante`) VALUES
(140987654, 'Administrador General', 'admin.prestalab@udp.cl', 'ENCARGADO', '+56955554444', 'ACTIVO', 1, '2025-09-29 17:30:00'),
(152398765, 'Marcela Soto', 'marcela.soto_d@mail.udp.cl', 'DOCENTE', '+56966554433', 'INACTIVO', 0, '2025-09-29 17:25:00'),
(165982311, 'Francisco Herrera', 'francisco.herrera_d@mail.udp.cl', 'DOCENTE', '+56977665544', 'ACTIVO', 1, '2025-09-29 17:20:00'),
(174892345, 'Camila Morales', 'camila.morales_s@mail.udp.cl', 'ESTUDIANTE', '+56988776655', 'DEUDOR', 1, '2025-09-29 17:15:00'),
(189453276, 'Ignacio Fernández', 'ignacio.fernandez_s@mail.udp.cl', 'ESTUDIANTE', '+56999887766', 'SUSPENDIDO', 0, '2025-09-29 17:10:00'),
(197407514, 'Rafael Campos', 'rafael.campos_s@mail.udp.cl', 'ESTUDIANTE', '+56942857599', 'ACTIVO', 1, '2025-09-29 17:03:07'),
(204587321, 'Valentina Rojas', 'valentina.rojas_s@mail.udp.cl', 'ESTUDIANTE', '+56991234567', 'ACTIVO', 1, '2025-09-29 17:05:00'),
(214166283, 'Juan Campos', 'juan.campos_s@mail.udp.cl', 'ESTUDIANTE', '+5698765432', 'ACTIVO', 1, '2025-09-30 15:12:09');

-- --------------------------------------------------------

--
-- Table structure for table `ventana`
--

CREATE TABLE `ventana` (
  `id` bigint NOT NULL,
  `solicitud_id` bigint NOT NULL,
  `item_existencia_id` bigint NOT NULL,
  `inicio` datetime NOT NULL,
  `fin` datetime NOT NULL
) ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `atraso`
--
ALTER TABLE `atraso`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`),
  ADD KEY `atrasoIDX1` (`prestamo_id`);

--
-- Indexes for table `configuracion_sistema`
--
ALTER TABLE `configuracion_sistema`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`),
  ADD UNIQUE KEY `clave` (`clave`),
  ADD UNIQUE KEY `clave_2` (`clave`);

--
-- Indexes for table `item`
--
ALTER TABLE `item`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`),
  ADD KEY `itemIDX1` (`nombre`,`tipo`);

--
-- Indexes for table `item_existencia`
--
ALTER TABLE `item_existencia`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`),
  ADD UNIQUE KEY `codigo` (`codigo`),
  ADD UNIQUE KEY `codigo_2` (`codigo`),
  ADD KEY `sede_id` (`sede_id`),
  ADD KEY `item_existenciaIDX1` (`item_id`);

--
-- Indexes for table `item_solicitud`
--
ALTER TABLE `item_solicitud`
  ADD PRIMARY KEY (`solicitud_id`,`item_id`),
  ADD KEY `item_solicitudIDX1` (`item_id`);

--
-- Indexes for table `lista_espera`
--
ALTER TABLE `lista_espera`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`),
  ADD KEY `solicitud_id` (`solicitud_id`),
  ADD KEY `item_id` (`item_id`),
  ADD KEY `lista_esperaIDX3` (`fecha_ingreso`);

--
-- Indexes for table `multa`
--
ALTER TABLE `multa`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`),
  ADD KEY `multaIDX1` (`prestamo_id`);

--
-- Indexes for table `notificacion`
--
ALTER TABLE `notificacion`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`),
  ADD KEY `notificacionIDX1` (`usuario_id`);

--
-- Indexes for table `prestamo`
--
ALTER TABLE `prestamo`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`),
  ADD KEY `solicitud_id` (`solicitud_id`),
  ADD KEY `prestamoIDX1` (`item_existencia_id`);

--
-- Indexes for table `sede`
--
ALTER TABLE `sede`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`);

--
-- Indexes for table `solicitud`
--
ALTER TABLE `solicitud`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`),
  ADD KEY `solicitudIDX1` (`usuario_id`);

--
-- Indexes for table `sugerencia`
--
ALTER TABLE `sugerencia`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indexes for table `usuario`
--
ALTER TABLE `usuario`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`),
  ADD UNIQUE KEY `correo` (`correo`),
  ADD UNIQUE KEY `correo_2` (`correo`),
  ADD KEY `usuarioIDX1` (`nombre`);

--
-- Indexes for table `ventana`
--
ALTER TABLE `ventana`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`),
  ADD KEY `solicitud_id` (`solicitud_id`),
  ADD KEY `item_existencia_id` (`item_existencia_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `atraso`
--
ALTER TABLE `atraso`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `configuracion_sistema`
--
ALTER TABLE `configuracion_sistema`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `item`
--
ALTER TABLE `item`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `item_existencia`
--
ALTER TABLE `item_existencia`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=121;

--
-- AUTO_INCREMENT for table `lista_espera`
--
ALTER TABLE `lista_espera`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `multa`
--
ALTER TABLE `multa`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `notificacion`
--
ALTER TABLE `notificacion`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `prestamo`
--
ALTER TABLE `prestamo`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `sede`
--
ALTER TABLE `sede`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `solicitud`
--
ALTER TABLE `solicitud`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `sugerencia`
--
ALTER TABLE `sugerencia`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `usuario`
--
ALTER TABLE `usuario`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=214166284;

--
-- AUTO_INCREMENT for table `ventana`
--
ALTER TABLE `ventana`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `atraso`
--
ALTER TABLE `atraso`
  ADD CONSTRAINT `atraso_ibfk_1` FOREIGN KEY (`prestamo_id`) REFERENCES `prestamo` (`id`);

--
-- Constraints for table `item_existencia`
--
ALTER TABLE `item_existencia`
  ADD CONSTRAINT `item_existencia_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `item` (`id`),
  ADD CONSTRAINT `item_existencia_ibfk_2` FOREIGN KEY (`sede_id`) REFERENCES `sede` (`id`);

--
-- Constraints for table `item_solicitud`
--
ALTER TABLE `item_solicitud`
  ADD CONSTRAINT `item_solicitud_ibfk_1` FOREIGN KEY (`solicitud_id`) REFERENCES `solicitud` (`id`),
  ADD CONSTRAINT `item_solicitud_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `item` (`id`);

--
-- Constraints for table `lista_espera`
--
ALTER TABLE `lista_espera`
  ADD CONSTRAINT `lista_espera_ibfk_1` FOREIGN KEY (`solicitud_id`) REFERENCES `solicitud` (`id`),
  ADD CONSTRAINT `lista_espera_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `item` (`id`);

--
-- Constraints for table `multa`
--
ALTER TABLE `multa`
  ADD CONSTRAINT `multa_ibfk_1` FOREIGN KEY (`prestamo_id`) REFERENCES `prestamo` (`id`);

--
-- Constraints for table `notificacion`
--
ALTER TABLE `notificacion`
  ADD CONSTRAINT `notificacion_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`);

--
-- Constraints for table `prestamo`
--
ALTER TABLE `prestamo`
  ADD CONSTRAINT `prestamo_ibfk_1` FOREIGN KEY (`item_existencia_id`) REFERENCES `item_existencia` (`id`),
  ADD CONSTRAINT `prestamo_ibfk_2` FOREIGN KEY (`solicitud_id`) REFERENCES `solicitud` (`id`);

--
-- Constraints for table `solicitud`
--
ALTER TABLE `solicitud`
  ADD CONSTRAINT `solicitud_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`);

--
-- Constraints for table `sugerencia`
--
ALTER TABLE `sugerencia`
  ADD CONSTRAINT `sugerencia_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuario` (`id`);

--
-- Constraints for table `ventana`
--
ALTER TABLE `ventana`
  ADD CONSTRAINT `ventana_ibfk_1` FOREIGN KEY (`solicitud_id`) REFERENCES `solicitud` (`id`),
  ADD CONSTRAINT `ventana_ibfk_2` FOREIGN KEY (`item_existencia_id`) REFERENCES `item_existencia` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
