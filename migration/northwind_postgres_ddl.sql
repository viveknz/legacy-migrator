-- Northwind database – PostgreSQL 16-compatible DDL migration
-- Generated from schema/Northwind_columns.txt and schema/Northwind_foreign_keys.txt
-- Tables are created in FK-dependency order; constraints are added at the end.

-- ============================================================
-- 1. Tables with no inbound FK dependencies
-- ============================================================

CREATE TABLE "Categories" (
    "CategoryID"   integer      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "CategoryName" varchar(15)  NOT NULL,
    "Description"  text,
    "Picture"      bytea
);

CREATE TABLE "Customers" (
    "CustomerID"   char(5)      NOT NULL PRIMARY KEY,
    "CompanyName"  varchar(40)  NOT NULL,
    "ContactName"  varchar(30),
    "ContactTitle" varchar(30),
    "Address"      varchar(60),
    "City"         varchar(15),
    "Region"       varchar(15),
    "PostalCode"   varchar(10),
    "Country"      varchar(15),
    "Phone"        varchar(24),
    "Fax"          varchar(24)
);

CREATE TABLE "CustomerDemographics" (
    "CustomerTypeID" char(10) NOT NULL PRIMARY KEY,
    "CustomerDesc"   text
);

CREATE TABLE "Employees" (
    "EmployeeID"      integer     GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "LastName"        varchar(20) NOT NULL,
    "FirstName"       varchar(10) NOT NULL,
    "Title"           varchar(30),
    "TitleOfCourtesy" varchar(25),
    "BirthDate"       timestamp,
    "HireDate"        timestamp,
    "Address"         varchar(60),
    "City"            varchar(15),
    "Region"          varchar(15),
    "PostalCode"      varchar(10),
    "Country"         varchar(15),
    "HomePhone"       varchar(24),
    "Extension"       varchar(4),
    "Photo"           bytea,
    "Notes"           text,
    "ReportsTo"       integer,
    "PhotoPath"       varchar(255)
);

CREATE TABLE "Region" (
    "RegionID"          integer  GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "RegionDescription" char(50) NOT NULL
);

CREATE TABLE "Shippers" (
    "ShipperID"   integer     GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "CompanyName" varchar(40) NOT NULL,
    "Phone"       varchar(24)
);

CREATE TABLE "Suppliers" (
    "SupplierID"   integer     GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "CompanyName"  varchar(40) NOT NULL,
    "ContactName"  varchar(30),
    "ContactTitle" varchar(30),
    "Address"      varchar(60),
    "City"         varchar(15),
    "Region"       varchar(15),
    "PostalCode"   varchar(10),
    "Country"      varchar(15),
    "Phone"        varchar(24),
    "Fax"          varchar(24),
    "HomePage"     text
);

-- ============================================================
-- 2. Tables that depend on Region
-- ============================================================

CREATE TABLE "Territories" (
    "TerritoryID"          varchar(20) NOT NULL PRIMARY KEY,
    "TerritoryDescription" char(50)    NOT NULL,
    "RegionID"             integer     NOT NULL
);

-- ============================================================
-- 3. Tables that depend on Categories / Suppliers
-- ============================================================

CREATE TABLE "Products" (
    "ProductID"       integer        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "ProductName"     varchar(40)    NOT NULL,
    "SupplierID"      integer,
    "CategoryID"      integer,
    "QuantityPerUnit" varchar(20),
    "UnitPrice"       numeric(19,4)  DEFAULT 0,
    "UnitsInStock"    smallint       DEFAULT 0,
    "UnitsOnOrder"    smallint       DEFAULT 0,
    "ReorderLevel"    smallint       DEFAULT 0,
    "Discontinued"    boolean        NOT NULL DEFAULT false
);

-- ============================================================
-- 4. Tables that depend on Customers / Employees / Shippers
-- ============================================================

CREATE TABLE "Orders" (
    "OrderID"        integer        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    "CustomerID"     char(5),
    "EmployeeID"     integer,
    "OrderDate"      timestamp,
    "RequiredDate"   timestamp,
    "ShippedDate"    timestamp,
    "ShipVia"        integer,
    "Freight"        numeric(19,4)  DEFAULT 0,
    "ShipName"       varchar(40),
    "ShipAddress"    varchar(60),
    "ShipCity"       varchar(15),
    "ShipRegion"     varchar(15),
    "ShipPostalCode" varchar(10),
    "ShipCountry"    varchar(15)
);

-- ============================================================
-- 5. Junction / child tables
-- ============================================================

CREATE TABLE "CustomerCustomerDemo" (
    "CustomerID"     char(5)  NOT NULL,
    "CustomerTypeID" char(10) NOT NULL,
    PRIMARY KEY ("CustomerID", "CustomerTypeID")
);

CREATE TABLE "EmployeeTerritories" (
    "EmployeeID"  integer     NOT NULL,
    "TerritoryID" varchar(20) NOT NULL,
    PRIMARY KEY ("EmployeeID", "TerritoryID")
);

CREATE TABLE "Order Details" (
    "OrderID"   integer       NOT NULL,
    "ProductID" integer       NOT NULL,
    "UnitPrice" numeric(19,4) NOT NULL DEFAULT 0,
    "Quantity"  smallint      NOT NULL DEFAULT 1,
    "Discount"  real          NOT NULL DEFAULT 0,
    PRIMARY KEY ("OrderID", "ProductID")
);

-- ============================================================
-- 6. Foreign key constraints
-- ============================================================

ALTER TABLE "CustomerCustomerDemo"
    ADD CONSTRAINT "FK_CustomerCustomerDemo"
        FOREIGN KEY ("CustomerTypeID") REFERENCES "CustomerDemographics" ("CustomerTypeID");

ALTER TABLE "Territories"
    ADD CONSTRAINT "FK_Territories_Region"
        FOREIGN KEY ("RegionID") REFERENCES "Region" ("RegionID");

ALTER TABLE "EmployeeTerritories"
    ADD CONSTRAINT "FK_EmployeeTerritories_Territories"
        FOREIGN KEY ("TerritoryID") REFERENCES "Territories" ("TerritoryID");

ALTER TABLE "EmployeeTerritories"
    ADD CONSTRAINT "FK_EmployeeTerritories_Employees"
        FOREIGN KEY ("EmployeeID") REFERENCES "Employees" ("EmployeeID");

ALTER TABLE "Employees"
    ADD CONSTRAINT "FK_Employees_Employees"
        FOREIGN KEY ("ReportsTo") REFERENCES "Employees" ("EmployeeID");

ALTER TABLE "Orders"
    ADD CONSTRAINT "FK_Orders_Employees"
        FOREIGN KEY ("EmployeeID") REFERENCES "Employees" ("EmployeeID");

ALTER TABLE "Products"
    ADD CONSTRAINT "FK_Products_Categories"
        FOREIGN KEY ("CategoryID") REFERENCES "Categories" ("CategoryID");

ALTER TABLE "CustomerCustomerDemo"
    ADD CONSTRAINT "FK_CustomerCustomerDemo_Customers"
        FOREIGN KEY ("CustomerID") REFERENCES "Customers" ("CustomerID");

ALTER TABLE "Orders"
    ADD CONSTRAINT "FK_Orders_Customers"
        FOREIGN KEY ("CustomerID") REFERENCES "Customers" ("CustomerID");

ALTER TABLE "Orders"
    ADD CONSTRAINT "FK_Orders_Shippers"
        FOREIGN KEY ("ShipVia") REFERENCES "Shippers" ("ShipperID");

ALTER TABLE "Products"
    ADD CONSTRAINT "FK_Products_Suppliers"
        FOREIGN KEY ("SupplierID") REFERENCES "Suppliers" ("SupplierID");

ALTER TABLE "Order Details"
    ADD CONSTRAINT "FK_Order_Details_Orders"
        FOREIGN KEY ("OrderID") REFERENCES "Orders" ("OrderID");

ALTER TABLE "Order Details"
    ADD CONSTRAINT "FK_Order_Details_Products"
        FOREIGN KEY ("ProductID") REFERENCES "Products" ("ProductID");
