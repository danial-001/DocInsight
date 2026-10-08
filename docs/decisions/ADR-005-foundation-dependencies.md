# ADR-005: Foundation dependencies and pip workflow

**Status:** approved  
**Decision ID:** D-008

The owner chose option B with the instruction “D-008: B I need pip packages”. The options used the same proposed runtime/framework pins, with uv or pip-tools as the Python dependency lock tool. Use pip-tools 7.6.1 to compile pinned requirements and install them with pip. The frontend uses npm and package-lock.json. The exact proposed foundation pins are recorded in IMPLEMENTATION_PLAN.md; their combined compatibility remains untested.

The dependency decision was followed by explicit WP-01a approval, authorizing installation and framework scaffolding within that scope. Package changes discovered during resolution need review if they change the approved set. The owner stated a preference for pip packages; no further rationale is inferred.

## WP-01a authorization and implementation update

Owner subsequently authorized installation/scaffolding within WP-01a with “Approved: D-009 A and WP-01a”. The approved direct pins resolved and both images built. Runtime requirements.txt, requirements-tools.txt and frontend/package-lock.json now exist. Browser check remains blocked; command compatibility checks passed. Earlier statement that WP-01a is proposed records the pre-approval state and is superseded by this authorization.

## WP-01b-5 extension and runtime-layout amendment

Owner approved D-028 A and Approved `WP-01b-5`: add exact google-auth2.61.0, google-auth-oauthlib1.5.0, requests2.34.2 and cryptography50.0.2; retain original framework/database pins and pip-tools7.6.1. requirements.txt now locks20 distributions. scripts/Compile-BackendRequirements.ps1 compiles the application lock using the existing hash-locked tooling in a disposable Linux container /opt/lock-venv; no Windows packages installed. Tool lock unchanged. Compiler header names the helper via CUSTOM_COMPILE_COMMAND rather than retaining an obsolete no-index command.

Owner initially required all libraries in a venv. After asking to use the previous installation layout, owner explicitly confirmed returning to container-wide Python with "Yup I men, yes, if there is no harm in it" in answer to the no-runtime-venv clarification. That condition is superseded; approved library pins remain unchanged. backend/Dockerfile installs hash-locked runtime packages into /usr/local Python during image build, running the server as app UID10001. Docker isolates these from Windows; a dedicated image avoids needing an additional runtime venv. Tooling venv remains separate/temporary. No claim that Docker protects against malicious dependencies or host compromise.

This machine required a Windows trusted public CA bundle for container downloads. Helper optionally mounts it read-only via CertificateBundlePath/PIP_CERT; image build optionally uses BuildKit secret pip_ca_bundle. It is not copied into the image/source, and certificate verification stays enabled. Gmail runtime HTTPS trust remains untested; download success is not provider integration. Actual checks and failures recorded in TESTING_AND_EVALUATION.md; component explanation in components/development-foundation.md.
