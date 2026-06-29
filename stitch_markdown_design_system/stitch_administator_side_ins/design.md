Design a clean, calm, easy-to-read government web application called "INS Survey Collection Platform" for the Institut National de la Statistique (INS). The users are government employees, many of them older and non-technical, so the design must be simple, spacious, and obvious — Material Design (Angular Material + Bootstrap), no gradients, no decorative imagery, no clutter.
Accessibility & simplicity rules (apply to every screen): body text 16px minimum, page titles 24–28px, high color contrast, buttons and inputs at least 48px tall, generous whitespace, clear visible labels above every field with short helper text, only ONE primary (filled) button per screen with secondary actions as outlined/text buttons, always show breadcrumbs on inner pages, and require a confirmation dialog before disabling/deleting/activating anything.
Colors: primary institutional blue #0B4F8A, accent #1B98A8, page background #F4F6F9, cards #FFFFFF, text #1F2933 / muted #667085, success #1E8E5A, warning #D98A00, danger #C0392B, borders #E2E8F0. Status chips use these colors with text labels (never color alone).
Typography: Inter / Roboto sans-serif.
App shell for all signed-in pages: a fixed left sidebar (white, INS logo + "INS Survey Platform" at top, large labelled menu items each with a simple line icon, the active item highlighted in blue, and at the bottom the user's name, role, and a clear "Sign out" button). A slim top bar showing the current page title, a notifications bell, and the user's name/avatar. Main area on light-gray background with white cards.
The four fixed navigations (use exactly these — never change the items or order):


System Administrator sidebar: Dashboard · Administrators · Account Managers · Users · Locked Accounts · Companies · Contacts · Surveys · Audit Logs · System Settings.

Account Manager sidebar: Dashboard · Companies · Contacts.

Survey Administrator sidebar: Dashboard · Surveys · Collection Monitoring · Questionnaires · Reports · Results.

Company Contact sidebar: Home · My Surveys · Results · My Profile.
Responsive (mobile ≤480px): the sidebar collapses into a hamburger drawer containing the same items in the same order; cards and tables stack into one column; every data table becomes a list of stacked cards (label-on-top, value-below); all buttons and inputs go full-width; the top bar keeps hamburger + title + avatar. Always output both the desktop and the mobile version of the screen.