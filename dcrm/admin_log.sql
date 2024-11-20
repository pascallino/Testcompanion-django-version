--
-- Create model User
--
CREATE TABLE `website_user` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `password` varchar(128) NOT NULL,
    `last_login` datetime(6) NULL,
    `userid` varchar(128) NULL UNIQUE,
    `email` varchar(128) NOT NULL UNIQUE,
    `first_name` varchar(128) NULL,
    `last_name` varchar(128) NULL,
    `role` varchar(10) NULL,
    `created_at` datetime(6) NOT NULL,
    `is_active` bool NOT NULL,
    `is_staff` bool NOT NULL,
    `is_superuser` bool NOT NULL,
    `company_id` varchar(255) NULL  -- Adjusted field name to match companyid
);

CREATE TABLE `website_user_groups` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` bigint NOT NULL,
    `group_id` integer NOT NULL
);

CREATE TABLE `website_user_user_permissions` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` bigint NOT NULL,
    `permission_id` integer NOT NULL
);

-- Adjust the foreign key constraint to match the companyid field
ALTER TABLE `website_user` 
ADD CONSTRAINT `website_user_company_id_fk_website_company_companyid` 
FOREIGN KEY (`companyid`) REFERENCES `website_company` (`companyid`);

ALTER TABLE `website_user_groups` 
ADD CONSTRAINT `website_user_groups_user_id_group_id_83920c88_uniq` 
UNIQUE (`user_id`, `group_id`);

ALTER TABLE `website_user_groups` 
ADD CONSTRAINT `website_user_groups_user_id_3e7ec47c_fk_website_user_id` 
FOREIGN KEY (`user_id`) REFERENCES `website_user` (`id`);

ALTER TABLE `website_user_groups` 
ADD CONSTRAINT `website_user_groups_group_id_9587eab2_fk_auth_group_id` 
FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);

ALTER TABLE `website_user_user_permissions` 
ADD CONSTRAINT `website_user_user_permis_user_id_permission_id_abfa6638_uniq` 
UNIQUE (`user_id`, `permission_id`);

ALTER TABLE `website_user_user_permissions` 
ADD CONSTRAINT `website_user_user_pe_user_id_2272c4c2_fk_website_u` 
FOREIGN KEY (`user_id`) REFERENCES `website_user` (`id`);

ALTER TABLE `website_user_user_permissions` 
ADD CONSTRAINT `website_user_user_pe_permission_id_e12e22f0_fk_auth_perm` 
FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`);
