# INS Statistical Survey Collection Platform
## Database Specification Document
**Version 2.0 (Updated After Supervisor Review)**

---

## 1. Introduction

This document describes the logical database architecture of the INS Statistical Survey Collection Platform.

The objective of this database is to support the complete lifecycle of statistical surveys conducted by the Institut National de la Statistique (INS), including:

- User management
- Role management
- Authentication
- Company management
- Contact management
- Survey management
- Passage management
- Sample management
- Collection monitoring
- Reporting
- Notification management
- Audit tracking

The architecture is designed to be modular, secure, scalable and maintainable.

---

## 2. Database Architecture Overview

The database is organized into the following domains:

```
Administration
├── Roles
├── Users
├── System Settings
├── Audit Logs

Authentication
├── OTP Codes
├── Login Attempts

Organization
├── Companies
├── Contacts
├── Sectors
├── Activities

Survey Management
├── Surveys
├── Survey Assignments
├── Periodicities
├── Survey Passages
├── Survey Questionnaires
├── Samples
├── Sample Companies
├── Survey Activations

Collection
├── Collection Tracking

Communication
├── Notifications

Results
├── Survey Result Files
```

---

## 3. Roles

### Purpose
Stores platform roles.

### Table
`roles`

### Fields
| Field | Type | Description |
|---|---|---|
| id | BIGINT PK | Unique identifier |
| code | VARCHAR(50) UNIQUE | Role code |
| name | VARCHAR(100) | Role name |
| description | TEXT | Description |
| created_at | DATETIME | Creation date |

### Initial Roles
- SYSTEM_ADMIN
- SURVEY_ADMIN
- ACCOUNT_MANAGER
- COMPANY_CONTACT

---

## 4. Users

### Purpose
Stores all platform accounts.

### Table
`users`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| role_id | BIGINT FK |
| email | VARCHAR(255) UNIQUE |
| password_hash | VARCHAR(255) |
| phone_number | VARCHAR(30) |
| email_verified | BOOLEAN |
| email_verified_at | DATETIME NULL |
| status | ENUM('ACTIVE','LOCKED','DISABLED') |
| first_login | BOOLEAN |
| preferred_language | ENUM('ar','fr','en') |
| password_only_until | DATETIME NULL |
| last_login_at | DATETIME NULL |
| created_at | DATETIME |
| updated_at | DATETIME |

### Business Rules
- Users are never deleted.
- Email must be unique.
- Passwords stored using bcrypt.
- Accounts disabled through status changes.

---

## 5. Companies

### Purpose
Stores participating companies.

### Table
`companies`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| identifier | VARCHAR(100) UNIQUE |
| company_name | VARCHAR(255) |
| tax_number | VARCHAR(100) |
| sector_id | BIGINT FK |
| activity_id | BIGINT FK |
| address | TEXT |
| governorate | VARCHAR(100) |
| postal_code | VARCHAR(20) |
| phone | VARCHAR(30) |
| email | VARCHAR(255) |
| status | ENUM('ACTIVE','INACTIVE') |
| created_at | DATETIME |
| updated_at | DATETIME |

### Business Rules
- Companies are never deleted.
- Identifiers must be unique.

---

## 6. Contacts

### Purpose
Stores company representatives.

### Table
`contacts`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| user_id | BIGINT FK |
| company_id | BIGINT FK |
| first_name | VARCHAR(100) |
| last_name | VARCHAR(100) |
| position | VARCHAR(255) |
| is_primary_contact | BOOLEAN |
| status | ENUM('ACTIVE','INACTIVE') |
| created_at | DATETIME |
| updated_at | DATETIME |

### Business Rules
- One company may have multiple contacts.
- All active contacts may access surveys assigned to their company.

---

## 7. Sectors

### Purpose
Reference table for business sectors.

### Table
`sectors`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| code | VARCHAR(50) |
| name_fr | VARCHAR(255) |
| name_ar | VARCHAR(255) |
| name_en | VARCHAR(255) |

---

## 8. Activities

### Purpose
Reference table for economic activities.

### Table
`activities`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| sector_id | BIGINT FK |
| code | VARCHAR(50) |
| name_fr | VARCHAR(255) |
| name_ar | VARCHAR(255) |
| name_en | VARCHAR(255) |

---

## 9. Periodicities

### Purpose
Stores survey frequencies.

### Table
`periodicities`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| code | VARCHAR(50) |
| name | VARCHAR(100) |

### Values
- MONTHLY
- QUARTERLY
- SEMESTRIAL
- ANNUAL
- BIENNIAL
- CUSTOM

---

## 10. Surveys

### Purpose
Stores INS surveys.

### Table
`surveys`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| code | VARCHAR(50) UNIQUE |
| name | VARCHAR(255) |
| description | TEXT |
| periodicity_id | BIGINT FK |
| status | ENUM('ACTIVE','INACTIVE','ARCHIVED') |
| created_by | BIGINT FK |
| created_at | DATETIME |
| updated_at | DATETIME |

### Business Rules
- Survey codes must be unique.
- Surveys are never deleted.
- Archived surveys remain available for consultation.

---

## 11. Survey Assignments

### Purpose
Assigns surveys to Survey Administrators.

### Table
`survey_assignments`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| survey_id | BIGINT FK |
| user_id | BIGINT FK |
| assigned_at | DATETIME |

### Business Rules
- A Survey Administrator may manage only surveys assigned to him.

---

## 12. Survey Passages

### Purpose
Represents collection campaigns.

### Table
`survey_passages`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| survey_id | BIGINT FK |
| year | INT |
| passage_number | INT |
| opening_date | DATETIME |
| closing_date | DATETIME |
| status | ENUM('DRAFT','READY','OPEN','CLOSED','ARCHIVED') |
| activated_by | BIGINT FK NULL |
| activated_at | DATETIME NULL |
| closed_by | BIGINT FK NULL |
| closed_at | DATETIME NULL |
| created_at | DATETIME |
| updated_at | DATETIME |

### Constraints
- Unique: `survey_id + year + passage_number`

### Business Rules
- Closing date must be greater than opening date.
- Passage may be activated only when questionnaire and sample exist.

---

## 13. Survey Questionnaires

### Purpose
Stores external questionnaire references.

### Table
`survey_questionnaires`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| passage_id | BIGINT FK |
| questionnaire_url | TEXT |
| questionnaire_pdf_path | TEXT |
| version | VARCHAR(50) |
| status | ENUM('ACTIVE','INACTIVE','ARCHIVED') |
| created_at | DATETIME |

### Important Note
Questionnaires are currently hosted on an external platform.
The synchronization mechanism between the questionnaire platform and INS platform is not yet defined.

The following items remain under clarification:
- Questionnaire opening tracking
- Questionnaire completion tracking
- Questionnaire response synchronization

---

## 14. Samples

### Purpose
Stores survey samples.

### Table
`samples`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| passage_id | BIGINT FK |
| uploaded_by | BIGINT FK |
| total_companies | INT |
| created_at | DATETIME |

---

## 15. Sample Companies

### Purpose
Stores companies selected in a sample.

### Table
`sample_companies`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| sample_id | BIGINT FK |
| company_id | BIGINT FK |
| created_at | DATETIME |

### Business Rules
- Duplicate companies are not allowed in the same sample.
- Company identifier validation required during import.

---

## 16. Survey Activations

### Purpose
Stores survey activation history.

### Table
`survey_activations`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| passage_id | BIGINT FK |
| activated_by | BIGINT FK |
| activated_at | DATETIME |
| notes | TEXT |

---

## 17. Collection Tracking

### Purpose
Tracks participation progress.

### Table
`collection_tracking`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| passage_id | BIGINT FK |
| company_id | BIGINT FK |
| status | ENUM('NOT_STARTED','IN_PROGRESS','COMPLETED') |
| first_access_at | DATETIME NULL |
| last_activity_at | DATETIME NULL |
| submitted_at | DATETIME NULL |
| created_at | DATETIME |

### Current Limitation
The update mechanism for these statuses depends on the future integration method with the external questionnaire platform.

---

## 18. Notifications

### Purpose
Stores all outgoing emails.

### Table
`notifications`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| user_id | BIGINT FK |
| channel | ENUM('EMAIL') |
| type | ENUM('OTP','ACTIVATION','INVITATION','REMINDER','RESET_PASSWORD') |
| recipient | VARCHAR(255) |
| status | ENUM('PENDING','SENT','FAILED') |
| provider_response | TEXT |
| retry_count | INT DEFAULT 0 |
| sent_at | DATETIME NULL |
| created_at | DATETIME |

---

## 19. OTP Codes

### Purpose
Stores authentication codes.

### Table
`otp_codes`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| user_id | BIGINT FK |
| code | VARCHAR(10) |
| expires_at | DATETIME |
| attempts | INT |
| created_at | DATETIME |

---

## 20. Login Attempts

### Purpose
Stores login history.

### Table
`login_attempts`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| user_id | BIGINT FK |
| ip_address | VARCHAR(50) |
| user_agent | TEXT |
| success | BOOLEAN |
| created_at | DATETIME |

---

## 21. Survey Result Files

### Purpose
Stores official INS survey results.

### Table
`survey_result_files`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| survey_id | BIGINT FK |
| sector_id | BIGINT FK |
| file_name | VARCHAR(255) |
| file_path | TEXT |
| file_type | ENUM('PDF','EXCEL') |
| uploaded_by | BIGINT FK |
| uploaded_at | DATETIME |

### Business Rules
- Only companies belonging to the corresponding sector may access the file.

---

## 22. Audit Logs

### Purpose
Stores critical actions performed on the platform.

### Table
`audit_logs`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| user_id | BIGINT FK |
| action | VARCHAR(255) |
| entity_type | VARCHAR(100) |
| entity_id | BIGINT |
| old_values | JSON |
| new_values | JSON |
| ip_address | VARCHAR(50) |
| created_at | DATETIME |

### Examples
- Company Created
- Company Updated
- Contact Disabled
- Survey Activated
- Sample Imported
- Data Exported

---

## 23. System Settings

### Purpose
Stores configurable parameters.

### Table
`system_settings`

### Fields
| Field | Type |
|---|---|
| id | BIGINT PK |
| setting_key | VARCHAR(100) UNIQUE |
| setting_value | TEXT |
| description | TEXT |
| updated_at | DATETIME |

### Examples
- OTP_EXPIRATION_MINUTES = 5
- MAX_LOGIN_ATTEMPTS = 3
- ACCOUNT_LOCK_HOURS = 24
- PASSWORD_ONLY_DURATION_HOURS = 1
- DEFAULT_LANGUAGE = fr
- EMAIL_PROVIDER = brevo

---

## 24. Entity Relationship Summary

```
roles
 ↓
users
 ↓
contacts
 ↓
companies

surveys
 ↓
survey_assignments

surveys
 ↓
survey_passages
 ↓
survey_questionnaires

survey_passages
 ↓
samples
 ↓
sample_companies
 ↓
companies

survey_passages
 ↓
collection_tracking

surveys
 ↓
survey_result_files

users
 ↓
audit_logs

users
 ↓
notifications
```

---

## 25. Pending Clarifications From INS

The following points remain to be validated before finalizing the database architecture:

1. How the external questionnaire platform communicates questionnaire opening.
2. How questionnaire completion is communicated to the INS platform.
3. How questionnaire responses become accessible to Survey Administrators.
4. Whether an API, webhook, synchronization service, or shared database exists between both systems.

These points may require additional tables and relationships in future versions.

---

*End of Database Specification*
*Version 2.0 — INS Statistical Survey Collection Platform*
