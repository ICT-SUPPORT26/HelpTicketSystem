const pool = require('./pool');
const bcrypt = require('bcryptjs');

async function initSchema() {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS "user" (
        id SERIAL PRIMARY KEY,
        username VARCHAR(64) UNIQUE NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(256) NOT NULL,
        full_name VARCHAR(100) NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'user',
        created_at TIMESTAMP DEFAULT NOW(),
        is_active BOOLEAN DEFAULT TRUE,
        is_verified BOOLEAN DEFAULT FALSE,
        verification_token VARCHAR(128),
        phone_number VARCHAR(20),
        is_approved BOOLEAN DEFAULT TRUE,
        approved_by_id INTEGER REFERENCES "user"(id),
        approved_at TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS category (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) UNIQUE NOT NULL,
        description VARCHAR(200),
        created_at TIMESTAMP DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS ticket (
        id SERIAL PRIMARY KEY,
        location VARCHAR(200) NOT NULL,
        description TEXT NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'open',
        priority VARCHAR(20) NOT NULL DEFAULT 'medium',
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        closed_at TIMESTAMP,
        closed_by_id INTEGER REFERENCES "user"(id),
        due_date TIMESTAMP,
        escalated_at TIMESTAMP,
        escalated_by_id INTEGER REFERENCES "user"(id),
        escalation_reason TEXT,
        created_by_id INTEGER REFERENCES "user"(id),
        category_id INTEGER REFERENCES category(id)
      );

      CREATE TABLE IF NOT EXISTS ticket_assignees (
        ticket_id INTEGER REFERENCES ticket(id) ON DELETE CASCADE,
        user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
        PRIMARY KEY (ticket_id, user_id)
      );

      CREATE TABLE IF NOT EXISTS comment (
        id SERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        is_internal BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW(),
        ticket_id INTEGER NOT NULL REFERENCES ticket(id) ON DELETE CASCADE,
        author_id INTEGER REFERENCES "user"(id)
      );

      CREATE TABLE IF NOT EXISTS attachment (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(200) NOT NULL,
        original_filename VARCHAR(200) NOT NULL,
        file_size INTEGER,
        content_type VARCHAR(100),
        created_at TIMESTAMP DEFAULT NOW(),
        ticket_id INTEGER NOT NULL REFERENCES ticket(id) ON DELETE CASCADE,
        uploaded_by_id INTEGER NOT NULL REFERENCES "user"(id)
      );

      CREATE TABLE IF NOT EXISTS ticket_history (
        id SERIAL PRIMARY KEY,
        ticket_id INTEGER NOT NULL REFERENCES ticket(id) ON DELETE CASCADE,
        user_id INTEGER NOT NULL REFERENCES "user"(id),
        action VARCHAR(100) NOT NULL,
        field_changed VARCHAR(100),
        old_value VARCHAR(200),
        new_value VARCHAR(200),
        timestamp TIMESTAMP DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS notification (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
        ticket_id INTEGER REFERENCES ticket(id) ON DELETE SET NULL,
        type VARCHAR(50) NOT NULL,
        title VARCHAR(200) NOT NULL,
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT FALSE,
        email_sent BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW(),
        read_at TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS notification_settings (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
        new_ticket_email BOOLEAN DEFAULT TRUE,
        new_ticket_app BOOLEAN DEFAULT TRUE,
        ticket_updated_email BOOLEAN DEFAULT TRUE,
        ticket_updated_app BOOLEAN DEFAULT TRUE,
        new_comment_email BOOLEAN DEFAULT TRUE,
        new_comment_app BOOLEAN DEFAULT TRUE,
        ticket_closed_email BOOLEAN DEFAULT TRUE,
        ticket_closed_app BOOLEAN DEFAULT TRUE,
        ticket_overdue_email BOOLEAN DEFAULT TRUE,
        ticket_overdue_app BOOLEAN DEFAULT TRUE,
        do_not_disturb BOOLEAN DEFAULT FALSE,
        dnd_start_time TIME,
        dnd_end_time TIME
      );

      CREATE TABLE IF NOT EXISTS access_log (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT NOW() NOT NULL,
        user_id INTEGER REFERENCES "user"(id),
        http_method VARCHAR(10) NOT NULL,
        endpoint VARCHAR(255) NOT NULL,
        ip_address VARCHAR(45),
        status_code INTEGER,
        response_time_ms INTEGER
      );
    `);

    await seedDefaults(client);
    console.log('Database schema initialized');
  } finally {
    client.release();
  }
}

async function seedDefaults(client) {
  const adminHash = await bcrypt.hash('admin123', 10);
  const internHash = await bcrypt.hash('Dctraining2023', 10);

  await client.query(`
    INSERT INTO "user" (username, email, password_hash, full_name, role, is_active, is_verified, is_approved)
    VALUES ($1, $2, $3, $4, 'admin', TRUE, TRUE, TRUE)
    ON CONFLICT (username) DO UPDATE SET
      password_hash = CASE
        WHEN EXCLUDED.password_hash NOT LIKE '$2%' THEN $3
        ELSE "user".password_hash
      END
  `, ['215030', 'admin@helpticketsystem.com', adminHash, 'System Administrator']);

  await client.query(`
    INSERT INTO "user" (username, email, password_hash, full_name, role, is_active, is_verified, is_approved)
    VALUES ($1, $2, $3, $4, 'intern', TRUE, TRUE, TRUE)
    ON CONFLICT (username) DO UPDATE SET
      password_hash = CASE
        WHEN EXCLUDED.password_hash NOT LIKE '$2%' THEN $3
        ELSE "user".password_hash
      END
  `, ['dctraining', 'intern@helpticketsystem.com', internHash, 'Dctraining']);
}

module.exports = { initSchema };
