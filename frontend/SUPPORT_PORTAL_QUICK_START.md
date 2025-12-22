# Support Portal - Quick Start Guide

## Access the Portal

**URL**: `/support-portal`

**Authorized Roles**:
- `support_agent` - Support team members
- `system_admin` - System administrators

## Key Pages

### 1. Dashboard (`/support-portal`)
Your command center with:
- Real-time ticket statistics
- Quick links to filtered views
- Recent tickets table
- Performance metrics (avg resolution time)

**Quick Actions**:
- View Unassigned Tickets → Click card or quick action button
- View High Priority → Filter for urgent/high priority
- View My Assigned → Go to "My Assigned" in sidebar

### 2. All Tickets (`/support-portal/tickets`)
Full ticket management with:
- **5 Filter Types**: Status, Priority, Category, Assignment, Search
- **Pagination**: 20 tickets per page
- **Sorting**: By created date, last updated
- **URL Persistence**: Filters saved in URL for sharing

**Common Workflows**:
1. Find unassigned tickets: Set "Assignment" → "Unassigned"
2. Find urgent issues: Set "Priority" → "Urgent"
3. Search ticket: Enter ticket # or subject in search box
4. View my tickets: Sidebar → "My Assigned"

### 3. Ticket Detail (`/support-portal/tickets/:id`)
Comprehensive ticket view:

**Left Side** (Main):
- Quick Actions (update status, priority, assignment)
- Full conversation history
- Reply/Internal Note composer

**Right Side** (Context):
- Business information (name, type)
- Customer details (name, email)
- Ticket metadata (category, timestamps)

## Key Features

### Internal Notes
**Purpose**: Agent-to-agent communication not visible to customers

**How to Use**:
1. Go to ticket detail
2. Type message in reply section
3. ✅ Check "Internal Note" checkbox
4. Click "Send Note"

**Visual Indicators**:
- Yellow background on message
- "Internal Note" badge
- Warning banner when composing

### Assigning Tickets

**Option 1**: Quick Assign to Yourself
- Click "Assign to Me" button in ticket detail

**Option 2**: Assign to Specific Agent
1. Click "Assign Agent" dropdown
2. Select agent (shows current ticket count)
3. Click "Assign" button

### Status Management

**Status Flow**:
1. **Open** → New ticket, needs attention
2. **In Progress** → Agent working on it
3. **Waiting Customer** → Replied, waiting for customer response
4. **Resolved** → Issue fixed, pending customer confirmation
5. **Closed** → Ticket complete

**How to Update**:
- Ticket Detail → Quick Actions → Update Status dropdown

### Priority Levels

**Color Coding**:
- 🔴 **Urgent**: Immediate attention required (red)
- 🟠 **High**: Important, handle soon (orange)
- 🟡 **Medium**: Normal priority (yellow)
- ⚪ **Low**: Can wait (gray)

### Canned Responses

**Purpose**: Pre-written responses for common issues

**How to Use**:
1. In ticket reply section
2. Click "Insert Template"
3. Browse templates by category
4. Click template to insert into reply
5. Edit as needed
6. Send

## Best Practices

### 1. Ticket Triage
When you start your shift:
1. Check Dashboard → Unassigned tickets
2. Check Dashboard → High Priority
3. Assign urgent tickets to yourself
4. Update status to "In Progress"

### 2. Customer Communication
**DO**:
- Use canned responses as starting point
- Personalize the message
- Update status to "Waiting Customer" after replying
- Be professional and clear

**DON'T**:
- Use internal notes for customer replies (they won't see them!)
- Leave tickets unassigned if you're working on them
- Forget to update status after actions

### 3. Internal Notes
**Use For**:
- Escalation information
- Technical details other agents need
- Investigation notes
- Handoff instructions

**Example**:
```
Internal Note: Verified issue is on our end.
Database timeout on invoice generation.
Dev team notified. ETA: 2 hours.
```

### 4. Collaboration
When handing off a ticket:
1. Add internal note with context
2. Reassign to other agent
3. Update status appropriately

## Common Scenarios

### Scenario 1: New Urgent Ticket
1. Dashboard shows red "High Priority" card
2. Click to view high priority tickets
3. Click ticket number to open
4. Click "Assign to Me"
5. Review business context on right sidebar
6. Update status to "In Progress"
7. Reply to customer or add internal note

### Scenario 2: Follow-up on Waiting Ticket
1. Go to "All Tickets"
2. Filter: Status → "Waiting Customer"
3. Filter: Assignment → "Assigned to Me"
4. Review tickets waiting for customer response
5. Check if customer replied
6. Update status based on resolution

### Scenario 3: Resolving a Ticket
1. Open ticket detail
2. Send final reply to customer
3. Update Status → "Resolved"
4. (Optional) Add internal note with resolution summary

### Scenario 4: Escalating to Another Agent
1. Add internal note: "Escalating to [Name] - [Reason]"
2. Use "Assign Agent" to reassign
3. Status remains "In Progress"

## Keyboard Shortcuts (Future)
_Coming soon: Keyboard shortcuts for faster navigation_

## Troubleshooting

**Problem**: Can't see Support Portal
- Check your role (must be support_agent or system_admin)
- Try logging out and back in
- Contact admin if issue persists

**Problem**: Stats not updating
- Click "Refresh" button on ticket list
- Dashboard auto-refreshes every 60 seconds

**Problem**: Can't assign ticket
- Verify you have permission
- Check if ticket is already assigned
- Refresh page and try again

## Support Portal URLs

- Dashboard: `/support-portal`
- All Tickets: `/support-portal/tickets`
- My Tickets: `/support-portal/my-tickets`
- Ticket Detail: `/support-portal/tickets/:id`

## Tips for Success

1. **Check Dashboard First**: Get overview before diving into tickets
2. **Use Filters**: Don't scroll through all tickets - filter intelligently
3. **Update Status**: Keep statuses current for accurate metrics
4. **Assign Tickets**: If you're working on it, assign it to yourself
5. **Use Internal Notes**: Document your work for other agents
6. **Templates Save Time**: Use canned responses, then personalize
7. **Business Context**: Always check right sidebar for customer info

## Getting Help

- Ask senior agents about best practices
- Use internal notes to ask questions
- Check ticket history to see how similar issues were handled
- System Admin can manage templates and settings

---

**Remember**: Good support is about clear communication, timely responses, and accurate tracking. Use the tools provided to deliver excellent customer service! 🎯
