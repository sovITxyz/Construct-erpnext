# Construct ERPNext

Custom Frappe app for ERPNext v16 targeting Latin American construction companies. Built to replicate [o4bi.com](https://o4bi.com) functionality. Primary deployment: **erp.gcs.sv** (GCS, El Salvador).

**License:** AGPL-3.0
**Requires:** Frappe, ERPNext, HRMS
**Currency:** USD
**Locale:** El Salvador (es)

---

## Modules

| Module | Purpose |
|--------|---------|
| Construct Projects | Budgets, cost entries, physical advancement, labor hours, equipment usage, change orders |
| Construct Production | SPC control charts, process traceability, corrective actions |
| Construct Maintenance | Maintenance routines, downtime tracking, FMEA failure analysis |
| Construct Admin | Invoice authorization, tax withholding, overtime, vacation, salary adjustments, reminders |
| Construct Finance | Check requests, deposit entries, collection documents, treasury, financial ratios |
| Construct Payroll | Payroll movements (bonuses, deductions, loans), cost distribution |
| Construct Security | Audit logging, permission controls |
| Construct Portal | Client-facing portal for projects, invoices, documents, advancement authorization |

## DocTypes

72 DocTypes across the 8 modules. Key ones:

- **Construction Budget** / **Budget Level** -- Multi-level project budgets with estimated vs actual tracking
- **Physical Advancement** -- Track project completion percentage over time
- **Project Cost Entry** -- Record actual costs against budget levels
- **Labor Hour Entry** / **Equipment Usage Log** -- Resource tracking
- **Check Request** -- Treasury check issuance workflow
- **Invoice Authorization** -- Approval gate before Purchase Invoice submission
- **Withholding Liquidation** -- Track tax withholdings by supplier, type, and period
- **Overtime Administration** -- Overtime records with El Salvador rate multipliers
- **Vacation Policy** / **Vacation Policy Rule** -- Country-aware vacation rules
- **Payroll Movement** -- Unified entry for bonuses, deductions, loans, and social security
- **Employee Loan** -- Internal employee loan tracking with installment deductions

## Reports (16 Script Reports)

| Report | Module |
|--------|--------|
| Budget Variance Analysis | Construct Projects |
| Budget vs Actual Cost | Construct Projects |
| Advancement vs Cost | Construct Projects |
| Advancement vs Schedule | Construct Projects |
| Physical Advancement Report | Construct Projects |
| Project Cost Summary | Construct Projects |
| Labor Cost by Activity | Construct Projects |
| Equipment Usage Report | Construct Projects |
| Material Acquisition Summary | Construct Projects |
| Material Distribution Report | Construct Projects |
| Revenue vs Billing | Construct Projects |
| Subcontract Status | Construct Projects |
| Change Order History | Construct Projects |
| Downtime Summary | Construct Maintenance |
| FMEA Report | Construct Maintenance |
| Maintenance Cost by Asset | Construct Maintenance |

## Client Portal

5 portal pages accessible to users with the **Customer** role:

| Route | Page |
|-------|------|
| `/project-portal` | Project list with progress bars and budget summary |
| `/project-portal/<project>` | Project detail with tasks and advancement history |
| `/client-invoices` | Invoice list with payment status badges |
| `/client-documents` | Document downloads organized by project |
| `/advancement-auth` | Review and authorize physical advancement reports |
| `/advancement-auth/<advancement>` | Single advancement authorization form |
| `/payment-history` | Payment entry history |

## Stock DocType Overrides

| DocType | Override Class | Purpose |
|---------|---------------|---------|
| Project | `ConstructProject` | Budget linkage, advancement calculations |
| Task | `ConstructTask` | Cost allocation to budget levels |
| Journal Entry | `ConstructJournalEntry` | Auto-posting for check requests |
| Salary Slip | `ConstructSalarySlip` | Injects Payroll Movement earnings/deductions |

## Document Event Hooks

| DocType | Event | Handler |
|---------|-------|---------|
| Purchase Invoice | validate | Tax withholding calculation (ISR, IVA retention, generic) |
| Purchase Invoice | on_submit | Invoice authorization gate |
| Sales Invoice | on_submit | Payment reminder scheduling |
| Stock Entry | on_submit | Material cost assignment to activities |
| Salary Slip | on_submit | Payroll cost distribution across projects |
| Physical Advancement | on_submit | Project progress update |
| Check Request | on_update_after_submit | Treasury status change handling |
| * (all) | after_insert, on_update, on_trash | Audit logging |

---

## El Salvador Localization

Full localization for El Salvador tax, payroll, and fiscal requirements.

### Spanish Translations

**File:** `construct_erpnext/translations/es.csv` (694 entries)

Frappe's standard translation system. All user-facing strings in Python (`_()`), JavaScript (`__()`), and Jinja templates (`{{ _() }}`) are translated. Covers:

- All 16 report column labels and filter labels
- All 72 DocType field labels
- Portal page text (7 HTML templates)
- Portal menu items
- Error messages and alerts from all controllers
- Email subjects and body text
- El Salvador-specific terms (IVA, ISR, ISSS, AFP, Aguinaldo, etc.)

### Tax System

**Files:** `construct_erpnext/setup/tax_setup.py`, `construct_erpnext/construct_admin/tax_withholding.py`

#### IVA (Impuesto al Valor Agregado) -- 13%

The install hook creates:

| Account | Type | Purpose |
|---------|------|---------|
| IVA Credito Fiscal | Asset | IVA paid on purchases (tax credit) |
| IVA Debito Fiscal | Liability | IVA collected on sales (tax debit) |
| Retencion ISR | Liability | ISR withholdings payable to government |
| Retencion IVA 1% | Liability | IVA advance retention (gran contribuyente) |

Tax templates created automatically:

- **IVA Compras 13%** -- Purchase tax template (adds 13% to net total)
- **IVA Ventas 13%** -- Sales tax template (adds 13% to net total)

#### Tax Withholding (3-tier system)

Applied automatically on Purchase Invoice validation:

| Tier | Rate | Condition |
|------|------|-----------|
| ISR Withholding | 10% | Supplier is Persona Natural with retention configured |
| IVA Retention | 1% | Company is Gran Contribuyente, supplier is not |
| Generic Retention | Variable | Fallback to supplier's `retention_percentage` field |

Tiers are evaluated in order. If ISR applies, the generic retention is skipped to avoid double-deduction.

#### Fiscal Document Types

Custom field `sv_document_type` on Sales Invoice:

| Type | Use |
|------|-----|
| CCF (Comprobante de Credito Fiscal) | B2B transactions |
| Consumidor Final | B2C transactions |
| Nota de Credito | Credit notes |
| Nota de Debito | Debit notes |
| Exportacion | Export invoices |

### Payroll System

**File:** `construct_erpnext/setup/payroll_setup.py`

#### Salary Components Created

| Component | Type | Rate | Notes |
|-----------|------|------|-------|
| ISSS Laboral | Deduction | 3% | Capped at salary ceiling (~$1,000/month) |
| ISSS Patronal | Earning | 7.5% | Employer contribution, same ceiling |
| AFP Laboral | Deduction | 7.25% | No ceiling |
| AFP Patronal | Earning | 8.75% | Employer contribution |
| Aguinaldo | Earning | Variable | Christmas bonus based on tenure |
| ISR Renta | Deduction | Progressive | Monthly income tax withholding |

#### Calculation Functions

All in `payroll_setup.py`, callable from Salary Structure formulas or custom scripts:

```python
from construct_erpnext.setup.payroll_setup import (
    calculate_isss,        # Returns {"employee": ..., "employer": ...}
    calculate_afp,         # Returns {"employee": ..., "employer": ...}
    calculate_aguinaldo,   # Returns dollar amount for an employee
    calculate_isr_renta,   # Returns monthly ISR withholding amount
)
```

#### ISR Monthly Tax Table

| Taxable Income (USD) | Rate | Fixed Amount |
|---------------------|------|-------------|
| $0.01 -- $472.00 | 0% | $0 |
| $472.01 -- $895.24 | 10% on excess | + $17.67 |
| $895.25 -- $2,038.10 | 20% on excess | + $60.00 |
| Over $2,038.10 | 30% on excess | + $288.57 |

#### Aguinaldo (Christmas Bonus)

| Tenure | Days of Salary |
|--------|---------------|
| < 1 year | Pro-rated from 10 days |
| 1 -- 3 years | 10 days |
| 3 -- 10 years | 15 days |
| 10+ years | 18 days |

Paid between December 12--20. Daily salary = monthly base / 30.

#### Vacation Rules

When a Vacation Policy has country = "El Salvador" and no manual rules, it auto-applies:

- **15 calendar days** paid vacation after 1 year of continuous service
- **30% bonus** on vacation pay (regular daily salary + 30%)

#### Overtime Rates

| Type | Multiplier | El Salvador Labor Code |
|------|-----------|----------------------|
| Diurna (daytime) | 2.0x | 100% surcharge |
| Nocturna (nighttime) | 2.25x | 125% surcharge |
| Standard | 1.5x | Generic fallback |
| Double | 2.0x | Generic double time |
| Custom | Manual | User-entered multiplier |

### Custom Fields on Stock DocTypes

All fields use module `Construct Admin` and are exported via the fixtures system.

#### Supplier

| Field | Type | Purpose |
|-------|------|---------|
| `sv_taxpayer_type` | Select | Gran/Mediano/Pequeno Contribuyente, Persona Natural, Otro |
| `retention_percentage` | Percent | Tax withholding rate for this supplier |
| `sv_nit` | Data | NIT (0000-000000-000-0) |
| `sv_nrc` | Data | NRC (Numero de Registro de Contribuyente) |

#### Customer

| Field | Type | Purpose |
|-------|------|---------|
| `sv_taxpayer_type` | Select | Gran/Mediano/Pequeno Contribuyente, Otro |
| `sv_nit` | Data | NIT |
| `sv_nrc` | Data | NRC |
| `sv_invoice_type` | Select | CCF or Consumidor Final (default fiscal document type) |

#### Company

| Field | Type | Purpose |
|-------|------|---------|
| `sv_gran_contribuyente` | Check | Whether company is a Large Taxpayer |
| `withholding_tax_account` | Link (Account) | Default withholding liability account |
| `sv_iva_credit_account` | Link (Account) | IVA Credito Fiscal account |
| `sv_iva_debit_account` | Link (Account) | IVA Debito Fiscal account |

#### Sales Invoice

| Field | Type | Purpose |
|-------|------|---------|
| `sv_document_type` | Select | CCF, Consumidor Final, Nota de Credito/Debito, Exportacion |
| `sv_authorization_number` | Data | DTE authorization number |

#### Employee

| Field | Type | Purpose |
|-------|------|---------|
| `sv_dui` | Data | DUI -- national ID (00000000-0) |
| `sv_nit` | Data | NIT |
| `sv_isss_number` | Data | ISSS affiliation number |
| `sv_afp_number` | Data | AFP account number |
| `sv_afp_provider` | Select | AFP Confia or AFP Crecer |

### Setup / Installation

**File:** `construct_erpnext/setup/install.py`

The `after_install` hook runs automatically when the app is installed. For each Company with country = "El Salvador":

1. Creates tax accounts and templates (`setup_el_salvador_taxes`)
2. Creates salary components (`setup_el_salvador_payroll`)
3. Creates custom fields on stock DocTypes (`_create_custom_fields`)

To run manually for a specific company:

```python
from construct_erpnext.setup.tax_setup import setup_el_salvador_taxes
from construct_erpnext.setup.payroll_setup import setup_el_salvador_payroll

setup_el_salvador_taxes("My Company Name")
setup_el_salvador_payroll("My Company Name")
```

---

## Roles

| Role | Purpose |
|------|---------|
| Construction Manager | Full access to project management DocTypes |
| Budget Controller | Budget creation and approval |
| Site Inspector | Physical advancement and quality entries |
| Construction Client | Portal access for clients |
| Subcontractor Portal | Limited portal access for subcontractors |
| Maintenance Engineer | Maintenance routines and failure analysis |
| Treasury Manager | Check requests, deposits, collections |
| Audit Administrator | Security audit log access |
| Payroll Cost Allocator | Payroll distribution across projects |

## Scheduler Events

| Frequency | Task |
|-----------|------|
| Daily | Send payment reminders for overdue invoices |
| Daily | Check preventive maintenance schedules |
| Hourly | Process audit event queue |

## Development

### Installation

```bash
bench get-app https://github.com/sovITxyz/Construct-erpnext.git
bench --site your-site install-app construct_erpnext
```

### Fixtures

Custom fields and roles are exported as fixtures. After modifying custom fields in the UI:

```bash
bench --site your-site export-fixtures --app construct_erpnext
```

### Adding Translations

Edit `construct_erpnext/translations/es.csv`. Format: `source_text,translated_text,context`

After editing, clear cache:

```bash
bench --site your-site clear-cache
```

### File Structure

```
construct_erpnext/
  construct_projects/     # Budgets, costs, advancement, reports
  construct_production/   # SPC, traceability, corrective actions
  construct_maintenance/  # Routines, downtime, FMEA
  construct_admin/        # Authorization, withholding, overtime, vacation
  construct_finance/      # Treasury, deposits, collections, ratios
  construct_payroll/      # Movements, loans, cost distribution
  construct_security/     # Audit logging, permissions
  construct_portal/       # Portal API and utilities
  overrides/              # Stock DocType controller overrides
  public/js/              # Client scripts for stock DocTypes
  setup/                  # El Salvador tax, payroll, and install hooks
  translations/           # es.csv (Spanish)
  www/                    # Portal HTML templates
  hooks.py                # App configuration
```
