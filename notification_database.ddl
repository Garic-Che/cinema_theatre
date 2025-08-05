CREATE SCHEMA IF NOT EXISTS content;

CREATE TABLE IF NOT EXISTS content.template (
    id uuid PRIMARY KEY,
    template TEXT,
    template_type TEXT DEFAULT '',
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    modified timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.content (
    id uuid PRIMARY KEY,
    key TEXT NOT NULL,
    value TEXT,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    modified timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.notification (
    id uuid PRIMARY KEY,
    template_id uuid NOT NULL REFERENCES content.template (id) ON DELETE CASCADE,
    content_id TEXT,
    sent boolean DEFAULT FALSE,
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    modified timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.schedule_notification (
    id uuid PRIMARY KEY,
    template_id uuid NOT NULL REFERENCES content.template (id) ON DELETE CASCADE,
    period bigint,
    next_send timestamp with time zone,
    once boolean DEFAULT FALSE,
    receiver_group_name TEXT DEFAULT 'all',
    created timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    modified timestamp with time zone
);

INSERT INTO content.template (id, template, template_type) VALUES (gen_random_uuid(), 'Тестовый шаблон уведомления', 'test');
INSERT INTO content.template (id, template, template_type) VALUES (gen_random_uuid(), '<h1>Новые лайки:</h1>
<ul>
  {% for id, name in zip(content, content_name) %}
    <li>
      <a href="/some/link/{{ id }}">{{ name }}</a>
    </li>
  {% endfor %}
</ul>', 'like');
INSERT INTO content.template (id, template, template_type) VALUES (gen_random_uuid(), '<h1>Новые комментарии:</h1>
<ul>
  {% for id, name in zip(content, content_name) %}
    <li>
      <a href="/some/link/{{ id }}">{{ name }}</a>
    </li>
  {% endfor %}
</ul>', 'comment');
INSERT INTO content.template (id, template, template_type) VALUES (gen_random_uuid(), 'Ваша подписка истечёт {{ content }}', 'subscription_expiration');
INSERT INTO content.template (id, template, template_type) VALUES (gen_random_uuid(), 'Ваша транзакция {{ content }} не прошла', 'transaction_failed');
INSERT INTO content.template (id, template, template_type) VALUES (gen_random_uuid(), 'Ваша транзакция {{ content }} прошла успешно', 'transaction_success');
INSERT INTO content.template (id, template, template_type) VALUES (gen_random_uuid(), 'Ваша транзакция {{ content }} не прошла из-за таймаута', 'transaction_timeout');