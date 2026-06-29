# INS Statistical Survey Collection Platform
## Functional Specification & Product Story
**Version 4.0 (Updated After Supervisor Review)**

---

## 1. Project Vision

The INS Statistical Survey Collection Platform is a centralized and secure web platform developed for the Institut National de la Statistique (INS).

The objective of the platform is to manage the complete lifecycle of statistical surveys conducted among companies, from survey planning and sample management to collection monitoring and reporting.

The platform acts as the central management system for INS and as the access portal for companies selected to participate in surveys.

The platform must provide:
- Secure authentication
- Survey management
- Passage management
- Sample management
- Company repository management
- Contact management
- Collection monitoring
- Reporting and exports
- Publication of survey results
- Communication between INS and participating companies

---

## 2. Business Process

The platform follows the official INS workflow:

```
Survey (Enquête)
 ↓
Passage
 ↓
Sample (Échantillon)
 ↓
Selected Companies
 ↓
Company Contacts
 ↓
Questionnaire Access
 ↓
Collection Monitoring
 ↓
Reports & Results
```

---

## 3. Actors

### System Administrator
Responsible for global platform administration.

**Permissions:**
- Manage administrators
- Manage account managers
- Manage users
- Manage companies
- Manage contacts
- Manage system settings
- View audit logs
- Access all surveys
- Resolve authentication issues

### Survey Administrator
Responsible for survey operations.

**Permissions:**
- Create surveys
- Manage passages
- Manage samples
- Configure questionnaires
- Activate collection campaigns
- Monitor collection
- Export survey data
- View questionnaires regardless of status
- View questionnaire responses (pending external system clarification)

Access rights are assigned per survey.

### Account Manager (Responsable des Comptes)
Responsible for company and contact management.

**Permissions:**
- Create companies
- Edit companies
- Search companies
- Disable companies
- Create contacts
- Edit contacts
- Search contacts
- Disable contacts

### Company Contact
Representative of a sampled company.

**Permissions:**
- Access assigned surveys
- Open questionnaires
- Download questionnaire PDF
- View collection status
- Download published survey results
- Update personal profile
- Change password

If a company belongs to a sample, all active contacts of that company may access the survey.

---

## 4. Authentication Module

### Login
All users authenticate using:
- Email
- Password

### Two-Factor Authentication
After password validation:
- A 6-digit OTP is sent by email.
- OTP expires after 5 minutes.
- OTP can be resent.
- Maximum 3 failed attempts.

After 3 failures:
- Account is locked for 24 hours.

### First Login
When a contact account is created:
1. Activation email sent.
2. Contact validates email.
3. Contact logs in.
4. System forces password change.
5. Password policy enforced.

### Login Recovery
System Administrator may:
- Search locked accounts.
- Enable password-only access for 1 hour.

---

## 5. User Management

### Administrators
System Administrator may:
- Create administrator
- Edit administrator
- Search administrator
- Disable administrator

### Account Managers
System Administrator may:
- Create account manager
- Edit account manager
- Search account manager
- Disable account manager

### User Monitoring
System Administrator may:
- Search all users
- View account status
- View login history
- View lock status

---

## 6. Company Management

### Company Repository
Stores:
- Identifier
- Company name
- Tax information
- Sector
- Activity
- Contact information
- Status

### Company Operations
System Administrator and Account Manager may:
- Create company
- Search company
- View company
- Edit company
- Disable company

Companies are never physically deleted.

### Company Import
Excel import supports:
- Bulk creation
- Duplicate detection
- Missing field detection
- Existing company detection

Administrator reviews import results before confirmation.

---

## 7. Contact Management

### Contact Repository
Stores:
- Personal information
- Position
- Company relationship
- Account information

### Contact Operations
System Administrator and Account Manager may:
- Create contact
- Edit contact
- Search contact
- Disable contact

### Contact Creation
System automatically:
- Creates user account
- Generates temporary password
- Sends activation email

---

## 8. Survey Management

### Survey Definition
A survey represents an INS statistical investigation.

**Examples:**
- EMI
- ESA
- ECA

### Survey Information
Fields:
- Code
- Name
- Description
- Periodicity
- Status

### Supported Periodicities
- Monthly
- Quarterly
- Semiannual
- Annual
- Biennial
- Custom

### Survey Operations
Survey Administrator may:
- Create survey
- Edit survey
- Archive survey
- Assign survey administrators

---

## 9. Passage Management

### Passage Definition
A passage represents a specific collection campaign for a survey.

### Passage Information
Fields:
- Survey
- Year
- Passage Number
- Opening Date
- Closing Date
- Status

### Status Values
- Draft
- Ready
- Open
- Closed
- Archived

### Questionnaire Configuration
Survey Administrator may:
- Configure questionnaire URL
- Upload questionnaire PDF
- Manage questionnaire versions

---

## 10. Sample Management

### Sample Definition
A sample is the list of companies selected for a passage.

### Sample Creation
Survey Administrator:
1. Selects survey.
2. Selects passage.
3. Uploads Excel file.

### Validation Rules
System validates:
- Existing companies
- Duplicate identifiers
- Invalid identifiers
- Missing identifiers

### Sample Consultation
Survey Administrator may:
- View selected companies
- Search selected companies
- Export sample list

---

## 11. Survey Activation

### Preconditions
A passage may be activated only if:
- Survey exists
- Passage exists
- Sample exists
- Questionnaire configured

### Activation Actions
System automatically:
- Creates collection tracking records
- Sends invitation emails
- Opens collection monitoring

### Invitation Email
Contains:
- Survey information
- Collection period
- Questionnaire PDF
- Platform URL

---

## 12. Collection Monitoring

### Dashboard
Survey Administrator may view:
- Total sampled companies
- Responding companies
- Pending companies
- Completion rate

### Monitoring by Survey
Indicators available:
- Survey
- Passage
- Year
- Status

### Company Statuses
- Not Started
- In Progress
- Completed

---

## 13. Questionnaire Consultation

Following supervisor feedback, Survey Administrators must be able to:
- View questionnaires regardless of status
- View questionnaires in progress
- View completed questionnaires
- Consult questionnaire responses

### Important Note
The technical implementation of this functionality depends on the integration mechanism with the external questionnaire platform and remains pending clarification.

The following questions remain open:
- How is questionnaire opening communicated to the INS platform?
- How is questionnaire completion communicated to the INS platform?
- How are questionnaire responses made available to the INS platform?

---

## 14. Reporting

Survey Administrator may:
- Generate collection reports
- Generate participation reports
- Generate statistical reports
- Export survey data

### Export Formats
- PDF
- Excel
- CSV

---

## 15. Survey Results Repository

INS may publish official survey results.

### Upload Results
Survey Administrator uploads:
- PDF
- Excel

Associated with:
- Survey
- Sector

### Download Results
Company contacts may:
- View results for their sector
- Download published files

---

## 16. Company Portal

After authentication, company contacts access a dashboard displaying:
- Assigned surveys
- Collection status
- Deadlines
- Available results

### Available Actions
- Open questionnaire
- Download questionnaire PDF
- View survey status
- Download survey results
- Update profile
- Change password

---

## 17. Audit & Traceability

The platform must record all critical actions.

### Examples
- Company creation
- Company modification
- Contact creation
- Contact disablement
- Survey activation
- Sample upload
- Export generation

### Each audit record contains:
- User
- Action
- Date
- Entity
- Old values
- New values

---

## 18. Role Management Rules

Permissions are not only role-based.

Permissions may also be scoped by:
- Survey
- Passage
- Company

### Examples
- A Survey Administrator may only access assigned surveys.
- A Survey Administrator may only manage passages of assigned surveys.
- Company contacts only access surveys linked to samples containing their company.

---

## 19. Current Open Architecture Question

Before development of collection tracking synchronization and questionnaire consultation modules, INS must clarify:

1. How the external questionnaire platform communicates questionnaire opening.
2. How questionnaire completion is communicated.
3. How responses are retrieved.
4. Whether an API, webhook, shared database, or synchronization mechanism exists.

This decision will directly impact:
- Collection Tracking
- Reporting
- Questionnaire Consultation
- Dashboard Statistics
- Database Design

---

*End of Specification*
*Version 4.0 — INS Statistical Survey Collection Platform*
