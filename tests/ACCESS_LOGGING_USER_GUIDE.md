# Access Logging System - User Guide

## Overview

The Help Ticket System now has a **comprehensive access logging system** that captures and displays every user activity, including:

- **Login/Logout Events** - Track when users enter and leave the system
- **All User Actions** - Every page visit, API call, and interaction
- **Response Metrics** - Response times and HTTP status codes
- **Activity Timelines** - Chronological view of what each user did
- **Session Tracking** - Group activities into login sessions

## Features

### 1. **Activity Logging (Automatic)**
- ✓ Every HTTP request is logged automatically
- ✓ Captures: timestamp, user, endpoint, HTTP method, status code, response time, IP address
- ✓ Logs are written efficiently using queue-based buffering (non-blocking)
- ✓ No performance impact on user experience

### 2. **Access Logs Dashboard**
- View all users grouped by activity
- See statistics: total activities, error rates, last activity time
- Pagination: 20 users per page for fast loading

### 3. **Activity Timeline (NEW)**
- Detailed chronological view of one user's activities
- Shows what they did, when, how long each action took
- Color-coded status codes (success/redirect/error)
- Session information with login/logout times

## How to Use

### Accessing the Logs

1. **Login as Admin**
   - Username: `215030`
   - Password: `admin123`

2. **Go to Access Logs**
   - Click menu → Admin → Access Logs
   - Or navigate directly to: `/access_logs`

### Viewing User Activity Summary

URL: `/access_logs`

This page shows:
- **Users Grid**: Card-based view of all users with their statistics
- **Statistics**: 
  - Total activities (logs)
  - Error count & rate
  - Last activity time
- **Quick Actions**: Buttons to view timeline or all activities
- **Pagination**: 20 users per page

### Viewing User Activity Timeline (NEW)

URL: `/access_logs/user_timeline/<user_id>`

Click "View Timeline" on any user card to see:

1. **Summary Statistics**
   - Total activities
   - Active sessions count
   - Error count
   - Average response time

2. **Activity Log Timeline**
   - Each activity in reverse chronological order (newest first)
   - For each activity shows:
     - **Timestamp**: When the action happened (Nairobi time)
     - **Method & Endpoint**: What API/page was accessed (GET /login, POST /ticket, etc.)
     - **IP Address**: Where the request came from
     - **Status Code**: ✓ 200-299 (Success, green), 300-399 (Redirect, blue), 400-499 (Client error, yellow), 500+ (Server error, red)
     - **Response Time**: How long the action took in milliseconds

3. **Sessions Table** (if available)
   - Session number
   - Login time
   - Number of activities in that session
   - Logout time (or "Still active")
   - Total duration of the session

### Viewing Detailed Access Logs

URL: `/access_logs/details`

Traditional table view with:
- All access log entries with full details
- Filtering by: user, status code, HTTP method, date range
- 100 logs per page
- Sortable columns

## What Gets Logged?

**Automatic Logging Captures:**
- ✓ Page views (`/login`, `/dashboard`, `/ticket/123`)
- ✓ API calls (search, filters, status updates)
- ✓ Form submissions (comments, ticket creation)
- ✓ File uploads/downloads
- ✓ Every request timestamp
- ✓ Response status and time

**Excluded from Logging (for performance):**
- ✗ Static assets (`/static/*`)
- ✗ User uploads directory (`/uploads/*`)
- ✗ File downloads (`/files/*`)

## Interpreting the Data

### Status Codes

| Code | Meaning | Color |
|------|---------|-------|
| 200-299 | Success ✓ | Green |
| 300-399 | Redirect | Blue |
| 400-499 | User/Client Error | Yellow |
| 500+ | Server Error | Red |

### Common Endpoints

| Endpoint | What It Does |
|----------|------------|
| `login` | User login attempt |
| `logout` | User logout |
| `dashboard` | Dashboard view |
| `ticket/<id>` | View/edit ticket |
| `comment/<id>` | Add/view comment |
| `api_*` | API calls (background requests) |

### Response Time Interpretation

| Time | Performance |
|------|-------------|
| < 50ms | Excellent |
| 50-200ms | Normal |
| 200-1000ms | Slow |
| > 1000ms | Very Slow - investigate |

## Example Scenarios

### Scenario 1: Track User Login Session

Step 1: User logs in
- You see: `GET login` with status 200 (success)

Step 2: User browses tickets
- You see: Series of `GET dashboard`, `GET ticket/123` calls
- Each shows response time and status

Step 3: User logs out
- You see: `GET logout` with status 302 (redirect to login page)

**Timeline shows:** Complete session with all actions in sequence

### Scenario 2: Investigate User Error

If you see a user with high error rate:

1. Go to Access Logs → Click user card
2. Click "View Timeline"
3. Look for status codes 400-599 (shown in yellow/red)
4. Check which endpoint caused the error
5. Look at response time to identify performance issues

### Scenario 3: Audit Specific Activities

1. Go to Access Logs → Details
2. Filter by User, Date Range, Status Code, or HTTP Method
3. See complete log of activities during that period
4. Export or analyze as needed

## Performance Notes

✓ **Optimized Design**
- Queue-based logging: Requests logged to memory queue instantly (< 1ms)
- Background thread flushes logs to database in batches every 5 seconds
- Zero impact on user request handling

✓ **Database Efficiency**
- Indexed columns: timestamp, user_id, endpoint, status_code, method
- Pagination reduces memory usage
- Automatic cleanup of old records (can be configured)

✓ **Connection Pool**
- Increased pool size: 50 connections (default 5)
- Max overflow: 100 connections
- Prevents "connection pool exhausted" errors

## Troubleshooting

### No logs appearing

1. Check middleware is enabled:
   ```bash
   python test_access_logging.py
   ```

2. Make some requests by interacting with the system

3. Refresh the access logs page after 5 seconds

### Some activities not shown

- Static files and uploads are excluded (by design)
- Only HTTP requests are logged
- Failed requests ARE logged with error status codes

### Performance issues on access_logs page

- Uses pagination (20 users per page)
- Navigate through pages instead of loading all at once
- Check database performance if all pages are slow

## Technical Details

### Logging Flow

```
User Request
    ↓
[before_request hook] - Record start time & IP
    ↓
[Request Processing] - Flask handles the request
    ↓
[after_request hook] - Create log entry, queue it
    ↓
[In-Memory Queue] - Fast (< 1ms), non-blocking
    ↓
[Background Thread] - Every 5s, batch-write to database
    ↓
[Database] - Stored for auditing & analysis
    ↓
[Admin Dashboard] - View logs with pagination & filters
```

### Configuration

**To enable/disable logging:**
- Edit `app.py` line ~97
- Uncomment: `AccessLoggerMiddleware(app)`
- Or comment out: `# AccessLoggerMiddleware(app)`

**To adjust log retention:**
- Edit `config.py`
- Modify pool settings if needed

## Common Questions

**Q: Is logging affecting performance?**
A: No. Queue-based buffering makes logging < 1ms per request.

**Q: What if the queue gets full?**
A: New logs are skipped with a warning. Queue is set to buffer 1000 entries.

**Q: Can I export logs?**
A: Yes, via SQL queries. Contact admin for export scripts.

**Q: Do I need to restart the app to enable logging?**
A: Yes, logging middleware is initialized when the app starts.

**Q: How long are logs kept?**
A: Currently indefinitely. Configure cleanup in database settings.

## Admin Tips

1. **Regular Monitoring**: Check access logs weekly for suspicious activity
2. **Error Investigation**: Filter by status code 500 to find system errors
3. **Performance Baseline**: Note average response times to detect degradation
4. **User Behavior**: Monitor for unusual access patterns (e.g., excessive failed logins)
5. **Audit Trail**: Keep logs for compliance and security purposes

---

**System Ready:** All user activities are now being captured and can be reviewed in the Access Logs dashboard!
