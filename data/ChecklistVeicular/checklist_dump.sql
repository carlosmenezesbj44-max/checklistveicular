BEGIN TRANSACTION;
CREATE TABLE itens_checklist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        veiculo_id INTEGER,
        nome_item TEXT,
        status TEXT,
        comentario TEXT,
        caminho_foto TEXT,
        caminho_thumb TEXT,
        FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
    );
INSERT INTO "itens_checklist" VALUES(1,1,'Farol Esq.','Danificado','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(2,1,'Farol Dir.','Desgastado','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(3,1,'Pisca Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(4,1,'Pisca Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(5,1,'Lanterna Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(6,1,'Lanterna Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(7,1,'Luz de ré','Danificado','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(8,1,'Luz de freio','Danificado','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(9,1,'Retrovisor Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(10,1,'Retrovisor Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(11,1,'Pneus Dianteiros','Danificado','PNEU COM RASGO ','item_11_20251125231300171793_pneu-rasgado.jpeg','thumb_item_11_20251125231300171793_pneu-rasgado.jpeg');
INSERT INTO "itens_checklist" VALUES(12,1,'Pneus Traseiros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(13,1,'Estepe','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(14,1,'Triângulo','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(15,1,'Macaco','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(16,1,'Chave de roda','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(17,1,'Limpador de para-brisa','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(18,1,'Vidros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(19,1,'Lataria','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(20,1,'Interior','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(21,1,'Fluido de freio','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(22,2,'Farol Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(23,2,'Farol Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(24,2,'Pisca Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(25,2,'Pisca Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(26,2,'Lanterna Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(27,2,'Lanterna Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(28,2,'Luz de ré','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(29,2,'Luz de freio','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(30,2,'Retrovisor Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(31,2,'Retrovisor Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(32,2,'Pneus Dianteiros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(33,2,'Pneus Traseiros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(34,2,'Estepe','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(35,2,'Triângulo','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(36,2,'Macaco','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(37,2,'Chave de roda','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(38,2,'Limpador de para-brisa','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(39,2,'Vidros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(40,2,'Lataria','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(41,2,'Interior','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(42,2,'Fluido de freio','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(43,2,'Água do Carro','Normal','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(44,3,'Farol Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(45,3,'Farol Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(46,3,'Pisca Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(47,3,'Pisca Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(48,3,'Lanterna Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(49,3,'Lanterna Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(50,3,'Luz de ré','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(51,3,'Luz de freio','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(52,3,'Retrovisor Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(53,3,'Retrovisor Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(54,3,'Pneus Dianteiros','Desgastado','','item_11_20251209122124286545_IMG-20251209-WA0229.jpeg','thumb_item_11_20251209122124286545_IMG-20251209-WA0229.jpeg');
INSERT INTO "itens_checklist" VALUES(55,3,'Pneus Traseiros','Desgastado','','item_12_20251209122124668939_IMG-20251209-WA0236.jpeg','thumb_item_12_20251209122124668939_IMG-20251209-WA0236.jpeg');
INSERT INTO "itens_checklist" VALUES(56,3,'Estepe','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(57,3,'Triângulo','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(58,3,'Macaco','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(59,3,'Chave de roda','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(60,3,'Limpador de para-brisa','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(61,3,'Vidros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(62,3,'Lataria','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(63,3,'Interior','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(64,3,'Fluido de freio','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(65,3,'Água do Carro','Normal','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(66,4,'Farol Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(67,4,'Farol Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(68,4,'Pisca Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(69,4,'Pisca Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(70,4,'Lanterna Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(71,4,'Lanterna Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(72,4,'Luz de ré','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(73,4,'Luz de freio','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(74,4,'Retrovisor Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(75,4,'Retrovisor Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(76,4,'Pneus Dianteiros','Desgastado','','item_11_20251209122125818262_IMG-20251209-WA0229.jpeg','thumb_item_11_20251209122125818262_IMG-20251209-WA0229.jpeg');
INSERT INTO "itens_checklist" VALUES(77,4,'Pneus Traseiros','Desgastado','','item_12_20251209122126118674_IMG-20251209-WA0236.jpeg','thumb_item_12_20251209122126118674_IMG-20251209-WA0236.jpeg');
INSERT INTO "itens_checklist" VALUES(78,4,'Estepe','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(79,4,'Triângulo','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(80,4,'Macaco','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(81,4,'Chave de roda','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(82,4,'Limpador de para-brisa','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(83,4,'Vidros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(84,4,'Lataria','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(85,4,'Interior','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(86,4,'Fluido de freio','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(87,4,'Água do Carro','Normal','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(88,5,'Farol Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(89,5,'Farol Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(90,5,'Pisca Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(91,5,'Pisca Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(92,5,'Lanterna Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(93,5,'Lanterna Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(94,5,'Luz de ré','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(95,5,'Luz de freio','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(96,5,'Retrovisor Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(97,5,'Retrovisor Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(98,5,'Pneus Dianteiros','Desgastado','','item_11_20251209122235488619_IMG-20251209-WA0229.jpeg','thumb_item_11_20251209122235488619_IMG-20251209-WA0229.jpeg');
INSERT INTO "itens_checklist" VALUES(99,5,'Pneus Traseiros','Desgastado','','item_12_20251209122235770092_IMG-20251209-WA0236.jpeg','thumb_item_12_20251209122235770092_IMG-20251209-WA0236.jpeg');
INSERT INTO "itens_checklist" VALUES(100,5,'Estepe','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(101,5,'Triângulo','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(102,5,'Macaco','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(103,5,'Chave de roda','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(104,5,'Limpador de para-brisa','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(105,5,'Vidros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(106,5,'Lataria','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(107,5,'Interior','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(108,5,'Fluido de freio','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(109,5,'Água do Carro','Normal','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(110,6,'Farol Esq.','Danificado','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(111,6,'Farol Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(112,6,'Pisca Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(113,6,'Pisca Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(114,6,'Lanterna Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(115,6,'Lanterna Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(116,6,'Luz de ré','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(117,6,'Luz de freio','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(118,6,'Retrovisor Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(119,6,'Retrovisor Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(120,6,'Pneus Dianteiros','Desgastado','','item_11_20251209122902521732_IMG-20251209-WA0389.jpeg','thumb_item_11_20251209122902521732_IMG-20251209-WA0389.jpeg');
INSERT INTO "itens_checklist" VALUES(121,6,'Pneus Traseiros','Desgastado','','item_12_20251209122902853208_IMG-20251209-WA0390.jpeg','thumb_item_12_20251209122902853208_IMG-20251209-WA0390.jpeg');
INSERT INTO "itens_checklist" VALUES(122,6,'Estepe','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(123,6,'Triângulo','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(124,6,'Macaco','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(125,6,'Chave de roda','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(126,6,'Limpador de para-brisa','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(127,6,'Vidros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(128,6,'Lataria','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(129,6,'Interior','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(130,6,'Fluido de freio','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(131,6,'Água do Carro','Normal','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(132,7,'Farol Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(133,7,'Farol Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(134,7,'Pisca Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(135,7,'Pisca Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(136,7,'Lanterna Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(137,7,'Lanterna Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(138,7,'Luz de ré','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(139,7,'Luz de freio','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(140,7,'Retrovisor Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(141,7,'Retrovisor Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(142,7,'Pneus Dianteiros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(143,7,'Pneus Traseiros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(144,7,'Estepe','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(145,7,'Triângulo','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(146,7,'Macaco','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(147,7,'Chave de roda','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(148,7,'Limpador de para-brisa','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(149,7,'Vidros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(150,7,'Lataria','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(151,7,'Interior','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(152,7,'Fluido de freio','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(153,7,'Água do Carro','Normal','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(154,8,'Farol Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(155,8,'Farol Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(156,8,'Pisca Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(157,8,'Pisca Dir.','Danificado','','item_4_20251209202718312809_IMG-20251209-WA0999.jpeg','thumb_item_4_20251209202718312809_IMG-20251209-WA0999.jpeg');
INSERT INTO "itens_checklist" VALUES(158,8,'Lanterna Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(159,8,'Lanterna Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(160,8,'Luz de ré','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(161,8,'Luz de freio','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(162,8,'Retrovisor Esq.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(163,8,'Retrovisor Dir.','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(164,8,'Pneus Dianteiros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(165,8,'Pneus Traseiros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(166,8,'Estepe','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(167,8,'Triângulo','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(168,8,'Macaco','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(169,8,'Chave de roda','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(170,8,'Limpador de para-brisa','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(171,8,'Vidros','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(172,8,'Lataria','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(173,8,'Interior','OK','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(174,8,'Fluido de freio','Desgastado','',NULL,NULL);
INSERT INTO "itens_checklist" VALUES(175,8,'Água do Carro','Normal','',NULL,NULL);
CREATE TABLE manutencao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                veiculo_id INTEGER NOT NULL,
                nome_peca TEXT NOT NULL,
                data_manutencao TEXT NOT NULL,
                quilometragem_atual TEXT NOT NULL,
                vida_util_km INTEGER,
                proxima_manutencao_km INTEGER,
                valor_peca REAL,
                mao_de_obra REAL,
                observacoes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
            );
CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            , email TEXT, reset_token TEXT, reset_token_expiration TIMESTAMP);
INSERT INTO "users" VALUES(1,'admin','scrypt:32768:8:1$KJRSbKRlz2ZIUqXU$9f5f4a2df96d884d13857a5dc1b143cb64db4a99260882f3546acb37cbedeebc253ba9dcac467e7c20601bfd4a5fb2fb41e686856a96e34f271cb3f7875b03f3',1,'2025-12-05 15:01:40',NULL,NULL,NULL);
INSERT INTO "users" VALUES(2,'vip','scrypt:32768:8:1$TtxeVXz1WgBYGiIF$aa4ba75640060cb7d8a676c9066e1fd53c47c7b4515c1344d48a5b4c3cae647e365294ab027baa26bc499c3cbc26ff5aa67aa5b160f3317787c4eb32fd439c0f',1,'2025-12-05 17:24:26','vip@example.com',NULL,NULL);
INSERT INTO "users" VALUES(3,'paulo','scrypt:32768:8:1$6eUEL5Rud7oAKDl8$18b3f81525bff5e6f5b4f4a9f5afa4df021b653386cf5e14ca224893a4a97281ce20ff9c116986b0b5180511238cf9cc94082bd8b5dc3e7ed25fd6ab721c9620',0,'2025-12-05 20:08:29','1',NULL,NULL);
INSERT INTO "users" VALUES(4,'dias ','scrypt:32768:8:1$SwDfcRYJaS8Hh9Wc$077ceb61c0e7ee5fd62a043ee0f08df894fb430f6df1959ae2d51ee5c5ec603e03caf0f0471dcfd03bcd0bd2b03d0e006699d0eb8c8b83693d85b68af0b6b1fd',0,'2025-12-05 20:14:02','0',NULL,NULL);
INSERT INTO "users" VALUES(5,'carlosm','scrypt:32768:8:1$1uT5yx30AqEW3ve2$c20cbd321aba3cdf41a544c9e23adcc6ed3795dbbe1e0c269d2311c3d84e51030c2a2ed72dd2859beb7ded2c289bd2e1aaf93524e7bd5adb0d2e687abfe95c24',0,'2025-12-05 20:48:30','carlosasm2019@outlook.com',NULL,NULL);
INSERT INTO "users" VALUES(6,'junio','scrypt:32768:8:1$lSPJiwEhfFEBLo7r$ed6227ddac2ca1b0c1a44e40e10bb8669162969ab32fdcb43d373d9a00d9a3906acff7c4ca85a93067b291d5d4c281940937350afc982951fbf087059551232d',0,'2025-12-09 11:30:51','jvaldecibeserradesantanajunior@gmail.com',NULL,NULL);
INSERT INTO "users" VALUES(7,'jonh','scrypt:32768:8:1$zXFShOuYCN4lRYoR$08418f5831d657ef3efc74d0b8aaec113037931101a2fd65e5b731d6af40624d29713e4712242252c93a9b4eefe8144ad160de6e6fd6c5ae49ed7aa5701d34cf',0,'2025-12-09 11:34:12','Jonhlennonagillity@gmail.com',NULL,NULL);
INSERT INTO "users" VALUES(8,'eduardo','scrypt:32768:8:1$F5u20rm6Ma2BFToU$86c81d5c7e2a07fc1e82b2292e5a7c73d07b9aae547c098651c95fcf9289f54a38f9ccccd9db3b246737ff678d9b63da8da4b9896a70c636dcc1c099e6fa7bb9',0,'2025-12-09 11:36:36','eduardolins809@gmail.com',NULL,NULL);
INSERT INTO "users" VALUES(9,'magda','scrypt:32768:8:1$j5ImpBOeFz2V6j3W$d21fe0ac462e3a595b51a8587bce32ab5c6a7a796dd7a7756fbcc0a1ba059f5391f09db2e14a2905dca41cf3c124edc5c3718bdb71270d3f389e78b54eed1960',0,'2025-12-09 12:37:15','',NULL,NULL);
CREATE TABLE veiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        condutor TEXT,
        placa TEXT,
        modelo TEXT,
        data TEXT,
        quilometragem TEXT,
        observacoes TEXT,
        foto_carro TEXT,
        tipo TEXT
    , oleo_data TEXT, oleo_km TEXT);
INSERT INTO "veiculos" VALUES(1,'carlos','QYE8359','STRADA','25/11/2025 20:12','12788990','','veic_20251125231259828176_fiat-strada-freedom-cs.webp','Carro',NULL,NULL);
INSERT INTO "veiculos" VALUES(2,'paulo teste','qtt9515','cg titan','05/12/2025 20:00','10000','tuf certo',NULL,'Carro','2025-12-17','23555');
INSERT INTO "veiculos" VALUES(3,'MARCOS VINICIUS ','RZL6E39','Start 160','09/12/2025 12:21','126184','Precisa trocar os 2 penel 
E fazer uma revisão geral e nessa revisão troca o óleo ','veic_20251209122123994400_IMG-20251209-WA0414.jpg','Moto','2025-11-06','25366');
INSERT INTO "veiculos" VALUES(4,'MARCOS VINICIUS ','RZL6E39','Start 160','09/12/2025 12:21','126184','Precisa trocar os 2 penel 
E fazer uma revisão geral e nessa revisão troca o óleo ','veic_20251209122125714543_IMG-20251209-WA0414.jpg','Moto','2025-11-06','25366');
INSERT INTO "veiculos" VALUES(5,'MARCOS VINICIUS ','RZL6E39','Start 160','09/12/2025 12:22','126184','Precisa trocar os 2 penel 
E fazer uma revisão geral e nessa revisão troca o óleo ','veic_20251209122235366636_IMG-20251209-WA0414.jpg','Moto','2025-11-06','25366');
INSERT INTO "veiculos" VALUES(6,'Ananias Francisco ','OHJ1689','Fan 150','09/12/2025 12:29','13058','Precisa troca os 2 penel troca a buzina e alguns elementos danificados precisa se troca com urgencia  e fazer uma revisão geral','veic_20251209122902108370_IMG-20251209-WA0399.jpeg','Moto','2025-11-06','12820');
INSERT INTO "veiculos" VALUES(7,'Dimas souza','OCH8I92','Fan 150','09/12/2025 17:53','4237','Necessário a Revisão completa e colocar uma buzina','veic_20251209175306725401_IMG-20251209-WA0530.jpeg','Moto','2025-11-06','3902');
INSERT INTO "veiculos" VALUES(8,'Valdeci ','PDD9642','Bros160','09/12/2025 20:27','92489','','veic_20251209202717768801_17653119985063037743412910979855.jpg','Moto','2025-11-06','91942');
CREATE INDEX idx_veiculos_placa ON veiculos(placa);
CREATE INDEX idx_veiculos_condutor ON veiculos(condutor);
CREATE INDEX idx_veiculos_modelo ON veiculos(modelo);
CREATE INDEX idx_itens_veiculo ON itens_checklist(veiculo_id);
CREATE INDEX idx_itens_status ON itens_checklist(status);
CREATE INDEX idx_manutencao_veiculo ON manutencao(veiculo_id);
CREATE INDEX idx_manutencao_data ON manutencao(data_manutencao);
CREATE INDEX idx_manutencao_peca ON manutencao(nome_peca);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('veiculos',8);
INSERT INTO "sqlite_sequence" VALUES('itens_checklist',175);
INSERT INTO "sqlite_sequence" VALUES('users',9);
COMMIT;
