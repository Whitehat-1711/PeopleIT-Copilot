CREATE TABLE employees (
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
('E103', 'Rohan Verma', 'rohan.v@company.com', '+91-98201-77889', 'Finance', 20, 'ThinkPad X1 Carbon');

-- Defense-in-depth: read-only DB role for the MCP server
CREATE USER readonly_user WITH PASSWORD 'readonly_pass';
GRANT CONNECT ON DATABASE company_db TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON employees TO readonly_user;