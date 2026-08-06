#!/usr/bin/env bash
# Copyright (c) 2026 Sizedalloy33
# SPDX-License-Identifier: Apache-2.0
# See LICENSE file in the project root for full license information.
DISABLE_FLAG="$HOME/.config/no-welcome-message"
GOLD="\033[38;2;232;203;45m"
RESET="\033[0m"
BOLD="\033[1m"

if [[ $- == *i* ]] && [ ! -f "$DISABLE_FLAG" ]; then
    VERSION=$(rpm-ostree status --json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['deployments'][0]['version'])" 2>/dev/null)

    echo ""
    echo -e "  ${GOLD}${BOLD}Welcome to PulsarOS ${RESET}"
    echo -e "  ${GOLD} pulsaros:${VERSION}${RESET}"
    echo ""
    echo -e "  ${BOLD}${GOLD}Command${RESET}                    │ Description"
    echo    "  ──────────────────────────────────|─────────────────────────────"
    echo    "  ujust --choose                    │ List all available commands"
    echo    "  fastfetch                         │ View system information"
    echo    "  brew help                         │ Manage command line packages"
    echo ""
    echo -e "  ${GOLD}•${RESET}  Report an issue https://github.com/sizedalloy33/PulsarOS-Based-on-Fedora/issues"
    echo ""
    echo "To disable this message, run: touch ~/.config/no-welcome-message"
    echo ""
fi
