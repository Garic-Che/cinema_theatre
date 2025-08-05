CREATE SCHEMA IF NOT EXISTS content;

CREATE TABLE IF NOT EXISTS content.subscription (
    id UUID PRIMARY KEY,
    role_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    amount FLOAT NOT NULL,
    currency VARCHAR(255) NOT NULL,
    period INTEGER NOT NULL,
    actual BOOLEAN NOT NULL DEFAULT TRUE,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS content.user_subscription (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    subscription_id UUID REFERENCES content.subscription(id),
    auto_pay_id VARCHAR(255),
    expires TIMESTAMP NOT NULL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS content.transaction (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    payment_id VARCHAR(255) NOT NULL,
    user_subscription_id UUID REFERENCES content.user_subscription(id),
    amount FLOAT NOT NULL,
    currency VARCHAR(255) NOT NULL,
    status_code INTEGER NOT NULL,
    transaction_type INTEGER NOT NULL,
    starts TIMESTAMP,
    ends TIMESTAMP,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Тестовые данные
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
INSERT INTO content.subscription (id, role_id, name, description, amount, currency, period) VALUES ('2efa8092-98e1-4009-a34e-8e1ef3c3b418', '30c911d7-e22f-42aa-9b86-433b1da0e5d2', 'Подписка 1', 'Описание подписки 1', 100, 'RUB', 30);
INSERT INTO content.subscription (id, role_id, name, description, amount, currency, period) VALUES ('7b3fa121-005c-448c-b120-820a874d92b1', '55bc01fe-3005-4bfe-81a9-db305c4db235', 'Подписка 2', 'Описание подписки 2', 200, 'RUB', 30);
INSERT INTO content.subscription (id, role_id, name, description, amount, currency, period) VALUES ('5e66611e-72e7-4614-8cd5-12e45f157fe0', '55bc01fe-3005-4bfe-81a9-db305c4db235', 'Подписка 3', 'Описание подписки 3', 30, 'RUB', 3);

INSERT INTO content.user_subscription (id, user_id, subscription_id, auto_pay_id, expires) VALUES ('aea76155-d9ee-4094-93cc-bdcc2cc0e414', 'de508489-c283-4400-856b-fbb2f510536d', '2efa8092-98e1-4009-a34e-8e1ef3c3b418', '1', '2025-06-18 12:00:00');
INSERT INTO content.user_subscription (id, user_id, subscription_id, auto_pay_id, expires) VALUES ('75c0d9cb-47e0-4c74-9de1-9937c06baa82', 'de508489-c283-4400-856b-fbb2f510536d', '7b3fa121-005c-448c-b120-820a874d92b1', NULL, '2025-06-25 12:00:00');

INSERT INTO content.transaction (id, user_id, payment_id, user_subscription_id, amount, currency, status_code, transaction_type, created, modified) VALUES (uuid_generate_v4(), 'de508489-c283-4400-856b-fbb2f510536d', uuid_generate_v4(), 'aea76155-d9ee-4094-93cc-bdcc2cc0e414', 100, 'RUB', 1, 1, '2025-06-18 12:00:00', '2025-06-18 12:00:00');
INSERT INTO content.transaction (id, user_id, payment_id, user_subscription_id, amount, currency, status_code, transaction_type, created, modified) VALUES (uuid_generate_v4(), 'de508489-c283-4400-856b-fbb2f510536d', uuid_generate_v4(), '75c0d9cb-47e0-4c74-9de1-9937c06baa82', 200, 'RUB', 1, 1, now(), now());