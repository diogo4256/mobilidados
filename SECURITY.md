# Security

streetfit downloads public data and, with the optional AI tools, sends text to the Claude API. Please report
security problems privately through GitHub's *Report a vulnerability* (Security tab) rather than in a public
issue.

Relevant areas: the source fetchers (they write files named after case configuration), the `discover` agent's
HTTP allowlist, and anything that could send local files or personal data to a third party unintentionally.
