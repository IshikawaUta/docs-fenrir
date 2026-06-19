// Init Lucide Icons
lucide.createIcons();

// Sidebar Toggle
const sidebar = document.getElementById('sidebar');
const toggleBtn = document.getElementById('sidebarToggle');
const overlay = document.getElementById('sidebarOverlay');
const closeBtn = document.getElementById('closeSidebar');
const rightSidebar = document.getElementById('rightSidebar');

// Auto-collapse sidebar on mobile
if (window.innerWidth <= 768) {
    if (sidebar) sidebar.classList.add('collapsed');
}

const toggleSidebar = () => {
    if (sidebar) sidebar.classList.toggle('collapsed');
};

if (toggleBtn) toggleBtn.addEventListener('click', toggleSidebar);
if (overlay) overlay.addEventListener('click', toggleSidebar);
if (closeBtn) closeBtn.addEventListener('click', toggleSidebar);

// Keyboard Shortcut for Sidebar (Ctrl + B)
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'b') {
        e.preventDefault();
        if (sidebar) sidebar.classList.toggle('collapsed');
    }
});

// Collapsible Sidebar Groups
document.querySelectorAll('.group-header').forEach(header => {
    header.addEventListener('click', () => {
        const targetId = header.getAttribute('data-target');
        const content = document.getElementById(targetId);
        const chevron = header.querySelector('.chevron-icon');
        
        if (content) content.classList.toggle('hidden');
        if (chevron) chevron.classList.toggle('rotated');
    });
});

// Copy Code Feature
document.querySelectorAll('pre').forEach(pre => {
    // Wrap pre in a container
    const container = document.createElement('div');
    container.className = 'code-container mb-6';
    pre.parentNode.insertBefore(container, pre);
    container.appendChild(pre);

    // Create copy button
    const button = document.createElement('button');
    button.className = 'copy-button';
    button.innerHTML = '<i data-lucide="copy" class="w-4 h-4"></i>';
    container.appendChild(button);

    button.addEventListener('click', () => {
        const code = pre.innerText;
        navigator.clipboard.writeText(code).then(() => {
            button.classList.add('copied');
            button.innerHTML = '<i data-lucide="check" class="w-4 h-4"></i>';
            lucide.createIcons();
            
            setTimeout(() => {
                button.classList.remove('copied');
                button.innerHTML = '<i data-lucide="copy" class="w-4 h-4"></i>';
                lucide.createIcons();
            }, 2000);
        });
    });
});

// Search Functionality
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');

let searchTimeout;
if (searchInput && searchResults) {
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            searchResults.classList.add('hidden');
            return;
        }

        searchTimeout = setTimeout(async () => {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.length > 0) {
                searchResults.innerHTML = data.map(result => `
                    <a href="/docs/${result.id}?highlight=${encodeURIComponent(query)}" class="block p-3 border-b border-gray-150 dark:border-gray-800 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors">
                        <div class="text-blue-600 dark:text-blue-400 font-medium text-xs mb-1">${result.title}</div>
                        <div class="text-[10px] text-gray-500 dark:text-gray-400 line-clamp-2">${result.snippet}</div>
                    </a>
                `).join('');
                searchResults.classList.remove('hidden');
            } else {
                searchResults.innerHTML = '<div class="p-3 text-[10px] text-gray-400">No results found</div>';
                searchResults.classList.remove('hidden');
            }
        }, 300);
    });

    // Close search when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('hidden');
        }
    });

    // Search Shortcut (/)
    document.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement !== searchInput) {
            e.preventDefault();
            searchInput.focus();
        }
    });
}

// Search Highlighting
const urlParams = new URLSearchParams(window.location.search);
const searchHighlight = urlParams.get('highlight');
if (searchHighlight) {
    const contentArea = document.querySelector('.editor-content');
    if (contentArea) {
        // Safety: escape special regex characters and only match text outside of HTML tags
        const escapedQuery = searchHighlight.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(<[^>]*>)|(${escapedQuery})`, 'gi');
        
        contentArea.innerHTML = contentArea.innerHTML.replace(regex, (match, p1, p2) => {
            if (p1) return p1; // It's an HTML tag, return it as is
            return `<span class="search-highlight">${p2}</span>`; // It's a text match, wrap it
        });
        
        // Scroll to first highlight
        const firstHighlight = document.querySelector('.search-highlight');
        if (firstHighlight) {
            firstHighlight.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
}

// Right Sidebar (TOC) ScrollSpy
const tocLinks = document.querySelectorAll('.right-sidebar .toc a');
const headings = Array.from(document.querySelectorAll('.editor-content h1, .editor-content h2, .editor-content h3, .editor-content h4'));
const mainContent = document.querySelector('main .overflow-y-auto');

if (tocLinks.length > 0 && headings.length > 0 && mainContent) {
    mainContent.addEventListener('scroll', () => {
        let current = "";
        const scrollPosition = mainContent.scrollTop + 100;

        headings.forEach(heading => {
            const headingTop = heading.offsetTop;
            if (scrollPosition >= headingTop) {
                current = heading.getAttribute('id');
            }
        });

        tocLinks.forEach(link => {
            link.classList.remove('active-toc');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active-toc');
            }
        });
    });
}

// Scroll to Top Logic
const scrollToTopBtn = document.getElementById('scrollToTop');
const contentArea = document.querySelector('main .overflow-y-auto');

if (contentArea && scrollToTopBtn) {
    contentArea.addEventListener('scroll', () => {
        if (contentArea.scrollTop > 300) {
            scrollToTopBtn.classList.remove('hidden');
        } else {
            scrollToTopBtn.classList.add('hidden');
        }
    });

    // Reset scroll button position on resize
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 1280 && rightSidebar && !rightSidebar.classList.contains('collapsed')) {
            scrollToTopBtn.style.right = '300px';
        } else {
            scrollToTopBtn.style.right = '40px';
        }
    });

    scrollToTopBtn.addEventListener('click', () => {
        contentArea.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // Keyboard Shortcut (T or Home key)
    document.addEventListener('keydown', (e) => {
        if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA') {
            return;
        }

        if (e.key.toLowerCase() === 't' || e.key === 'Home') {
            e.preventDefault();
            contentArea.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }
    });
}

// Theme Toggle & Dropdown Menu
const themeToggle = document.getElementById('themeToggle');
const mobileThemeToggle = document.getElementById('mobileThemeToggle');
const moreMenuBtn = document.getElementById('moreMenuBtn');
const moreMenuDropdown = document.getElementById('moreMenuDropdown');
const htmlEl = document.documentElement;
const themeIcon = document.getElementById('themeIcon');
const themeText = document.getElementById('themeText');

// Check local storage or default to light
const currentTheme = localStorage.getItem('theme') || 'light';
htmlEl.className = currentTheme;
updateThemeUI(currentTheme);

const toggleTheme = () => {
    const activeTheme = htmlEl.classList.contains('dark') ? 'light' : 'dark';
    htmlEl.className = activeTheme;
    localStorage.setItem('theme', activeTheme);
    updateThemeUI(activeTheme);
    
    // Auto-hide the dropdown menu on action
    if (moreMenuDropdown) {
        moreMenuDropdown.classList.add('hidden');
    }
};

if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
}

if (mobileThemeToggle) {
    mobileThemeToggle.addEventListener('click', toggleTheme);
}

// Robust Clipboard Copy Helper
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        return new Promise((resolve, reject) => {
            try {
                const textArea = document.createElement("textarea");
                textArea.value = text;
                textArea.style.top = "0";
                textArea.style.left = "0";
                textArea.style.position = "fixed";
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                const successful = document.execCommand('copy');
                document.body.removeChild(textArea);
                if (successful) {
                    resolve();
                } else {
                    reject(new Error("execCommand failed"));
                }
            } catch (err) {
                reject(err);
            }
        });
    }
}

// Elegant Toast Helper
function showToast(message) {
    let toast = document.getElementById('toastNotification');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toastNotification';
        toast.className = 'fixed bottom-10 left-1/2 transform -translate-x-1/2 bg-neutral-900 dark:bg-neutral-200 text-white dark:text-neutral-900 px-4 py-2 rounded-lg shadow-xl z-[2000] text-xs font-medium transition-all duration-300 opacity-0 translate-y-2 pointer-events-none';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.offsetHeight; // trigger reflow
    toast.classList.remove('opacity-0', 'translate-y-2');
    toast.classList.add('opacity-100', 'translate-y-0');
    
    setTimeout(() => {
        toast.classList.remove('opacity-100', 'translate-y-0');
        toast.classList.add('opacity-0', 'translate-y-2');
    }, 2000);
}

// Share Handler Function
function triggerShare() {
    if (navigator.share) {
        navigator.share({
            title: document.title,
            url: window.location.href
        }).catch(err => {
            console.error("Error sharing:", err);
        });
    } else {
        // Clipboard Fallback
        copyToClipboard(window.location.href).then(() => {
            showToast("Link copied to clipboard!");
        }).catch(err => {
            console.error("Failed to copy link:", err);
        });
    }
}

// Share Functionality (using Event Delegation to capture click targets on SVG/path elements)
document.addEventListener('click', (e) => {
    if (e.target.closest('#shareBtn')) {
        triggerShare();
    }
});

// Toggle moreMenuDropdown (mobile) or rightSidebar (desktop)
if (moreMenuBtn) {
    moreMenuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (window.innerWidth < 768) {
            if (moreMenuDropdown) {
                moreMenuDropdown.classList.toggle('hidden');
            }
        } else {
            if (rightSidebar) {
                rightSidebar.classList.toggle('collapsed');
                // Reposition scroll-to-top button
                if (scrollToTopBtn && window.innerWidth >= 1280) {
                    scrollToTopBtn.style.right = rightSidebar.classList.contains('collapsed') ? '40px' : '300px';
                }
            }
        }
    });

    document.addEventListener('click', (e) => {
        if (moreMenuDropdown && !moreMenuBtn.contains(e.target) && !moreMenuDropdown.contains(e.target)) {
            moreMenuDropdown.classList.add('hidden');
        }
    });
}

// Keyboard Shortcuts for Share (S) and More / Right Sidebar (M)
document.addEventListener('keydown', (e) => {
    if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA') {
        return;
    }

    if (e.key.toLowerCase() === 's') {
        e.preventDefault();
        triggerShare();
    } else if (e.key.toLowerCase() === 'm') {
        e.preventDefault();
        const moreMenuBtn = document.getElementById('moreMenuBtn');
        if (moreMenuBtn) moreMenuBtn.click();
    }
});

function updateThemeUI(theme) {
    const mobileThemeIcon = document.getElementById('mobileThemeIcon');
    const mobileThemeText = document.getElementById('mobileThemeText');

    if (theme === 'dark') {
        if (themeIcon) {
            themeIcon.setAttribute('data-lucide', 'moon');
            themeIcon.classList.add('text-yellow-300');
        }
        if (themeText) themeText.textContent = 'Dark Mode';

        if (mobileThemeIcon) {
            mobileThemeIcon.setAttribute('data-lucide', 'moon');
            mobileThemeIcon.classList.add('text-yellow-300');
        }
        if (mobileThemeText) mobileThemeText.textContent = 'Dark Mode';
    } else {
        if (themeIcon) {
            themeIcon.setAttribute('data-lucide', 'sun');
            themeIcon.classList.remove('text-yellow-300');
        }
        if (themeText) themeText.textContent = 'Light Mode';

        if (mobileThemeIcon) {
            mobileThemeIcon.setAttribute('data-lucide', 'sun');
            mobileThemeIcon.classList.remove('text-yellow-300');
        }
        if (mobileThemeText) mobileThemeText.textContent = 'Light Mode';
    }
    if (window.lucide) lucide.createIcons();
}

// Final icons rendering
lucide.createIcons();