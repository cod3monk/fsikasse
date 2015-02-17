BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS `account` (
    `name`  TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS `unit` (
    `name`      TEXT PRIMARY KEY,
    `symbol`    TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS `transfer` (
    `from_id`        INTEGER,
    `to_id`          INTEGER,
    `valuable_id`    INTEGER NOT NULL,
    `amount`         INTEGER NOT NULL,
    `transaction_id` INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS `transaction` (
    `comment`   TEXT,
    `datetime`  TEXT
);
CREATE TABLE IF NOT EXISTS `valuable` (
    `name`          TEXT NOT NULL UNIQUE,
    `unit_name`     INTEGER NOT NULL,
    `price`         INTEGER NOT NULL,
    `image_path`    TEXT,
    `product`       INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS `user` (
    `name`               TEXT NOT NULL UNIQUE,
    `account_id`         INTEGER NOT NULL UNIQUE,
    `mail`               TEXT,
    `image_path`         TEXT,
    `browsable`          INTEGER NOT NULL DEFAULT 1,
    `direct_payment`     INTEGER NOT NULL DEFAULT 0,
    `allow_edit_profile` INTEGER NOT NULL DEFAULT 1,
    `active`             INTEGER NOT NULL DEFAULT 1
);

CREATE VIEW IF NOT EXISTS `account_valuable_balance` AS 
    SELECT 
        account.name AS account_name,
        account.rowid AS account_id,
        valuable.name AS valuable_name,
        valuable.rowid AS valuable_id,
        ifnull((SELECT sum(ifnull(amount,0)) FROM transfer WHERE to_id = account.rowid AND valuable_id = valuable.rowid),0)-ifnull((SELECT sum(ifnull(amount,0)) FROM transfer WHERE from_id = account.rowid AND valuable_id = valuable.rowid),0) AS balance,
        valuable.unit_name AS unit_name
    FROM account, valuable;

INSERT INTO `account` (`rowid`, `name`) VALUES (1, 'FSI: Graue Kasse');
INSERT INTO `account` (`rowid`, `name`) VALUES (2, 'FSI: Blaue Kasse');
INSERT INTO `account` (`rowid`, `name`) VALUES (3, 'FSI: Bankkonto');
INSERT INTO `account` (`rowid`, `name`) VALUES (4, 'FSI: Lager/Kühlschrank');
INSERT INTO `account` (`rowid`, `name`) VALUES (5, 'Gäste');
INSERT INTO `account` (`rowid`, `name`) VALUES (6, 'Materialsammlung');

INSERT INTO `user` (`name`, `account_id`, `browsable`, `direct_payment`, `allow_edit_profile`) 
    VALUES ("Gäste", 5, 0, 1, 0);
INSERT INTO `user` (`name`, `account_id`, `browsable`, `allow_edit_profile`) 
    VALUES ("Materialsammlung", 6, 0, 0);

INSERT INTO `unit` (`name`, `symbol`) VALUES ('Cent', '¢');
INSERT INTO `unit` (`name`, `symbol`) VALUES ('Flasche', 'Fl.');
INSERT INTO `unit` (`name`, `symbol`) VALUES ('Stück', 'St.');

INSERT INTO `valuable` (`name`, `unit_name`, `price`, `image_path`, `product`) 
    VALUES ('Euro', 'Cent', 1, NULL, 0);
INSERT INTO `valuable` (`name`, `unit_name`, `price`, `image_path`)
    VALUES ('Club-Mate', 'Flasche', 60, 'products/Loscher-Club-Mate.png');
INSERT INTO `valuable` (`name`, `unit_name`, `price`, `image_path`)
    VALUES ('ICE-T', 'Flasche', 60, 'products/Loscher-ICE-T.png');
INSERT INTO `valuable` (`name`, `unit_name`, `price`, `image_path`)
    VALUES ('Wintermate', 'Flasche', 60, 'products/Loscher-Winter-Mate.png');
INSERT INTO `valuable` (`name`, `unit_name`, `price`, `image_path`)
    VALUES ('Mate-Cola', 'Flasche', 60, 'products/Loscher-Mate-Cola.png');
INSERT INTO `valuable` (`name`, `unit_name`, `price`, `image_path`)
    VALUES ('Apfelschorle', 'Flasche', 60, 'products/Loscher-Apfelschorle.png');
INSERT INTO `valuable` (`name`, `unit_name`, `price`, `image_path`)
    VALUES ('Apfelsaft', 'Flasche', 60, 'products/Loscher-Apfelsaft.png');
INSERT INTO `valuable` (`name`, `unit_name`, `price`, `image_path`)
    VALUES ('Bier', 'Flasche', 90, 'products/Bier.png');
INSERT INTO `valuable` (`name`, `unit_name`, `price`, `image_path`)
    VALUES ('Orangensaft', 'Flasche', 60, 'products/Loscher-Orangensaft.png');
INSERT INTO `valuable` (`name`, `unit_name`, `price`, `image_path`)
    VALUES ('Wasser', 'Flasche', 30, 'products/Loscher-Tafelwasser.png');
COMMIT;

