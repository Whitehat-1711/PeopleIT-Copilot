CREATE TABLE IF NOT EXISTS employees (
    emp_id VARCHAR(10) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    department VARCHAR(50) NOT NULL,
    leave_balance INT NOT NULL,
    laptop_model VARCHAR(50) NOT NULL
);

INSERT INTO employees (emp_id, full_name, email, phone, department, leave_balance, laptop_model) VALUES
('E101', 'Aarav Sharma', 'aarav.s@company.com', '+91-98201-11223', 'Engineering', 14, 'MacBook Pro 16'),
('E102', 'Priya Patel', 'priya.p@company.com', '+91-98201-44556', 'Marketing', 6, 'Dell XPS 15'),
('E103', 'Rohan Verma', 'rohan.v@company.com', '+91-98201-77889', 'Finance', 20, 'ThinkPad X1 Carbon')
ON CONFLICT (emp_id) DO NOTHING;

-- Enable and FORCE Row-Level Security on employees table
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE employees FORCE ROW LEVEL SECURITY;

-- Defense-in-depth: read-only DB role for the MCP server
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readonly_user') THEN
        CREATE USER readonly_user WITH PASSWORD 'readonly_pass';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE company_db TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;

-- Policy enforcing session-scoped emp_id via app.emp_id
DROP POLICY IF EXISTS employee_isolation_policy ON employees;
CREATE POLICY employee_isolation_policy ON employees
    FOR SELECT
    TO readonly_user
    USING (emp_id = NULLIF(current_setting('app.emp_id', true), ''));

-- Expose v_self_service view with only needed columns (sensitive phone/email hidden)
CREATE OR REPLACE VIEW v_self_service WITH (security_barrier = true) AS
SELECT emp_id, full_name, department, leave_balance, laptop_model
FROM employees
WHERE emp_id = NULLIF(current_setting('app.emp_id', true), '');

-- Grant SELECT on employees (filtered by RLS) and v_self_service view
GRANT SELECT ON employees TO readonly_user;
GRANT SELECT ON v_self_service TO readonly_user;

-- Task C4: Tickets table for escalation
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id VARCHAR(20) PRIMARY KEY,
    emp_id VARCHAR(10) NOT NULL,
    category VARCHAR(50) NOT NULL,
    summary TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
GRANT SELECT, INSERT ON tickets TO readonly_user;
