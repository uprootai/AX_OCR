---
description: Track user-reported issue in KNOWN_ISSUES.md
---

Please track this issue in KNOWN_ISSUES.md following the workflow:

## When User Reports "안된다" (It doesn't work)

1. **Acknowledge** the issue in your response
2. **Add to KNOWN_ISSUES.md** with details using this template:

```markdown
### Issue #X: [Title]

**Status**: 🔴/🟠/🟡 **OPEN**
**Severity**: [Critical/High/Medium/Low]
**Component**: [API name]
**Discovered**: [Date]
**Reported By**: User

**Symptoms**:
- [What's happening]
- [Error messages]
- [Expected vs Actual behavior]

**Impact**:
- [Who/what is affected]
- [Severity of impact]

**Root Cause**: [If known, otherwise "Under investigation"]

**Workaround**: [Temporary solution if available]

**Investigation Steps**:
1. [ ] Check logs
2. [ ] Reproduce issue
3. [ ] Identify root cause
4. [ ] Apply fix
5. [ ] Verify resolution

**Related**:
- Files: [paths]
- Issues: [links]

**Notes**:
- [Additional context]
```

3. **Investigate** root cause
4. **Document** findings in the issue
5. **Update ROADMAP.md** to track resolution

## When User Reports "잘된다" (It works)

1. **Mark issue as RESOLVED** in KNOWN_ISSUES.md
2. **Move to Resolved Issues section**
3. **Add resolution details**:
   - Resolution time
   - What worked
   - Lessons learned
4. **Update ROADMAP.md** with [x]
5. **Document** in verification report
