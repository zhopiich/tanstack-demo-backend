CREATE TABLE submitters (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    tier TEXT NOT NULL CHECK (tier IN ('free', 'pro', 'verified'))
);

CREATE TABLE auth_users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'reviewer')),
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE auth_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES auth_users (id) ON DELETE CASCADE,
    refresh_token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    rotated_at TEXT,
    revoked_at TEXT
);

CREATE TABLE submissions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 100),
    status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected', 'flagged')),
    submitter_id TEXT NOT NULL REFERENCES submitters (id),
    content_type TEXT NOT NULL CHECK (content_type IN ('article', 'image', 'video', 'link')),
    content_url TEXT NOT NULL,
    thumbnail_url TEXT,
    score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    flag_count INTEGER NOT NULL CHECK (flag_count >= 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE submission_tags (
    submission_id TEXT NOT NULL REFERENCES submissions (id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    position INTEGER NOT NULL CHECK (position >= 0),
    PRIMARY KEY (submission_id, position)
);

CREATE TABLE submission_articles (
    submission_id TEXT PRIMARY KEY REFERENCES submissions (id) ON DELETE CASCADE,
    word_count INTEGER NOT NULL CHECK (word_count >= 1),
    reading_time INTEGER NOT NULL CHECK (reading_time >= 1)
);

CREATE TABLE submission_images (
    submission_id TEXT PRIMARY KEY REFERENCES submissions (id) ON DELETE CASCADE,
    width INTEGER NOT NULL CHECK (width >= 1),
    height INTEGER NOT NULL CHECK (height >= 1)
);

CREATE TABLE submission_videos (
    submission_id TEXT PRIMARY KEY REFERENCES submissions (id) ON DELETE CASCADE,
    duration INTEGER NOT NULL CHECK (duration >= 1),
    resolution TEXT NOT NULL CHECK (resolution IN ('480p', '720p', '1080p', '4k'))
);

CREATE TABLE submission_links (
    submission_id TEXT PRIMARY KEY REFERENCES submissions (id) ON DELETE CASCADE,
    domain TEXT NOT NULL,
    is_behind_paywall INTEGER NOT NULL CHECK (is_behind_paywall IN (0, 1))
);

CREATE TABLE reviews (
    submission_id TEXT PRIMARY KEY REFERENCES submissions (id) ON DELETE CASCADE,
    reviewer_name TEXT NOT NULL,
    reviewer_email TEXT NOT NULL,
    verdict TEXT NOT NULL CHECK (verdict IN ('approved', 'rejected')),
    reason TEXT NOT NULL CHECK (length(reason) >= 10),
    reviewed_at TEXT NOT NULL
);
