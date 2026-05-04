CREATE TABLE IF NOT EXISTS `airports` (
	`airport_id` INTEGER NOT NULL UNIQUE PRIMARY KEY AUTOINCREMENT,
	`iata_code` TEXT NOT NULL UNIQUE,
	`name` TEXT NOT NULL,
	`city` TEXT NOT NULL,
	`country` TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS `aircrafts` (
	`aircraft_id` INTEGER NOT NULL UNIQUE PRIMARY KEY AUTOINCREMENT,
	`reg_number` TEXT NOT NULL UNIQUE,
	`model` TEXT NOT NULL,
	`capacity` INTEGER NOT NULL,
	`status` TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS `flights` (
	`flight_id` INTEGER NOT NULL UNIQUE PRIMARY KEY AUTOINCREMENT,
	`flight_number` TEXT NOT NULL,
	`origin_id` INTEGER NOT NULL,
	`dest_id` INTEGER NOT NULL,
	`aircraft_id` INTEGER NOT NULL,
	`departure_time` TEXT NOT NULL,
	`arrival_time` TEXT NOT NULL,
	`base_price` REAL NOT NULL,
	`status` TEXT NOT NULL,
	FOREIGN KEY (`origin_id`) REFERENCES `airports`(`airport_id`),
	FOREIGN KEY (`dest_id`) REFERENCES `airports`(`airport_id`),
	FOREIGN KEY (`aircraft_id`) REFERENCES `aircrafts`(`aircraft_id`)
);
CREATE TABLE IF NOT EXISTS `bookings` (
	`booking_id` INTEGER NOT NULL UNIQUE PRIMARY KEY AUTOINCREMENT,
	`passenger_id` INTEGER NOT NULL,
	`flight_id` INTEGER NOT NULL,
	`seat_number` TEXT NOT NULL,
	`class` TEXT NOT NULL,
	`price` REAL NOT NULL,
	`status` TEXT NOT NULL,
	`booked_at` TEXT NOT NULL,
	FOREIGN KEY (`passenger_id`) REFERENCES `passengers`(`passenger_id`),
	FOREIGN KEY (`flight_id`) REFERENCES `flights`(`flight_id`)
);
CREATE TABLE IF NOT EXISTS `passengers` (
	`passenger_id` INTEGER NOT NULL UNIQUE PRIMARY KEY AUTOINCREMENT,
	`last_name` TEXT NOT NULL,
	`first_name` TEXT NOT NULL,
	`passport_num` TEXT NOT NULL UNIQUE,
	`email` TEXT NOT NULL UNIQUE,
	`phone` TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS `crew_members` (
	`crew_id` INTEGER NOT NULL UNIQUE PRIMARY KEY AUTOINCREMENT,
	`last_name` TEXT NOT NULL,
	`first_name` TEXT NOT NULL,
	`role` TEXT NOT NULL,
	`license_num` TEXT NOT NULL UNIQUE,
	`license_exp` TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS `flight_crew` (
	`id` INTEGER NOT NULL UNIQUE PRIMARY KEY AUTOINCREMENT,
	`flight_id` INTEGER NOT NULL,
	`crew_id` INTEGER NOT NULL,
	`position` TEXT NOT NULL,
	FOREIGN KEY (`flight_id`) REFERENCES `flights`(`flight_id`),
	FOREIGN KEY (`crew_id`) REFERENCES `crew_members`(`crew_id`)
);