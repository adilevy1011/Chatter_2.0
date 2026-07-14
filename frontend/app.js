const SERVER_URL = window.location.origin;
const socket = io(SERVER_URL, { transports: ['websocket'] });
console.log('Chatter web client loaded', SERVER_URL);

// --- DOM Declarations ---

const attachmentPreview = document.getElementById('attachment-preview');
const attachmentPreviewContent = document.getElementById('attachment-preview-content');
const attachmentPreviewCancel = document.getElementById('attachment-preview-cancel');

const replyPreview = document.getElementById('reply-preview');
const replyPreviewSender = document.getElementById('reply-preview-sender');
const replyPreviewText = document.getElementById('reply-preview-text');
const replyPreviewCancel = document.getElementById('reply-preview-cancel');


const editMessageModal = document.getElementById('edit-message-modal');
const editMessageInput = document.getElementById('edit-message-input');
const editMessageSave = document.getElementById('edit-message-save');
const editMessageCancel = document.getElementById('edit-message-cancel');
const editMessageClose = document.getElementById('edit-message-close');
const editMessageStatus = document.getElementById('edit-message-status');

let editingMessage = null;


const appLoadingScreen = document.getElementById('app-loading-screen');

const groupAddContactList = document.getElementById('group-add-contact-list');

const groupAddMemberPanel = document.getElementById('group-add-member-panel');
const groupAddMemberInput = document.getElementById('group-add-member-input');
const groupAddMemberSubmit = document.getElementById('group-add-member-submit');
const groupAddMemberCancel = document.getElementById('group-add-member-cancel');
const groupMemberStatus = document.getElementById('group-member-status');
const groupAddMemberButton = document.getElementById('group-add-member-button');

const confirmModal = document.getElementById('confirm-modal');
const confirmTitle = document.getElementById('confirm-title');
const confirmMessage = document.getElementById('confirm-message');
const confirmClose = document.getElementById('confirm-close');
const confirmYes = document.getElementById('confirm-yes');
const confirmNo = document.getElementById('confirm-no');

let pendingConfirmAction = null;

const addContactStatus = document.getElementById('add-contact-status');
const groupCreateStatus = document.getElementById('group-create-status');

const chatLayoutWrapper = document.querySelector('.chat-layout');
const mobileBackButton = document.getElementById('mobile-back-button');

const fileInput = document.getElementById('file-input');
const attachButton = document.getElementById('attach-button');

const authScreen = document.getElementById('auth-screen');
const mainScreen = document.getElementById('main-screen');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const authStatus = document.getElementById('auth-status');
const mainStatus = document.getElementById('main-status');
const usernameDisplay = document.getElementById('username-display');
const currentUserPanel = document.getElementById('current-user');
const contactList = document.getElementById('contact-list');
const chatTitle = document.getElementById('chat-title');
let loadMoreButton = null;
let loadMoreWrapper = null;
const messageList = document.getElementById('message-list');
const messageInput = document.getElementById('message-input');
const composer = document.querySelector('.composer');
const sendButton = document.getElementById('send-button');

const settingsModal = document.getElementById('settings-modal');
const settingsButton = document.getElementById('settings-button');
const settingsModalClose = document.getElementById('settings-modal-close');
const optChangePassword = document.getElementById('opt-change-password');
const passwordChangeForm = document.getElementById('password-change-form');
const settingsMenuOptions = document.getElementById('settings-menu-options');
const changePasswordBack = document.getElementById('change-password-back');

const currentPassInput = document.getElementById('settings-current-password');
const newPassInput = document.getElementById('settings-new-password');
const changePassSubmit = document.getElementById('change-password-submit');
const settingsStatus = document.getElementById('settings-status');

const loginButton = document.getElementById('login-button');
const registerButton = document.getElementById('register-button');
const addContactButton = document.getElementById('add-contact-button');
const createGroupButton = document.getElementById('create-group-button');
const logoutButton = document.getElementById('logout-button');
const tabLogin = document.getElementById('tab-login');
const tabRegister = document.getElementById('tab-register');
const groupCreationPanel = document.getElementById('group-creation-panel');
const groupNameInput = document.getElementById('group-name-input');
const groupMembersList = document.getElementById('group-members-list');
const groupCreateSubmit = document.getElementById('group-create-submit');
const groupCreateCancel = document.getElementById('group-create-cancel');
const addContactPanel = document.getElementById('add-contact-panel');
const addContactInput = document.getElementById('add-contact-input');
const addContactSubmit = document.getElementById('add-contact-submit');
const addContactCancel = document.getElementById('add-contact-cancel');
const seeMembersButton = document.getElementById('see-members-button');
const themeToggleButton = document.getElementById('theme-toggle');
const themeModeText = document.getElementById('theme-mode-text');

// Toolbar menu elements
const toolbarActionButton = document.getElementById('toolbar-action-button');
const toolbarMenu = document.getElementById('toolbar-menu');

// Modals
const pdfModal = document.getElementById('pdf-modal');
const pdfClose = document.getElementById('pdf-close');
const pdfTitle = document.getElementById('pdf-title');
const pdfCanvas = document.getElementById('pdf-canvas');
const pdfRenderArea = document.getElementById('pdf-render-area');
const pdfPrev = document.getElementById('pdf-prev');
const pdfNext = document.getElementById('pdf-next');
const pdfPageInfo = document.getElementById('pdf-page-info');
const pdfZoomIn = document.getElementById('pdf-zoom-in');
const pdfZoomOut = document.getElementById('pdf-zoom-out');
const pdfZoomLabel = document.getElementById('pdf-zoom-label');

let pdfDoc = null;
let pdfPageNumber = 1;
let pdfScale = 1.2;
let pdfRendering = false;
let pdfPendingPage = null;

const imageModal = document.getElementById('image-modal');
const imageClose = document.getElementById('image-close');
const imageViewerImg = document.getElementById('image-viewer-img');
const imageSave = document.getElementById('image-save');
let currentImageUrl = '';
let currentImageName = '';
const imageZoomIn = document.getElementById('image-zoom-in');
const imageZoomOut = document.getElementById('image-zoom-out');

const videoModal = document.getElementById('video-modal');
const videoClose = document.getElementById('video-close');
const videoViewer = document.getElementById('video-viewer');


let imageZoomLevel = 1;

const membersModal = document.getElementById('members-modal');
const membersModalTitle = document.getElementById('members-modal-title');
const membersModalClose = document.getElementById('members-modal-close');
const membersList = document.getElementById('members-list');

const receiptsModal = document.getElementById('receipts-modal');
const receiptsModalClose = document.getElementById('receipts-modal-close');
const receiptsList = document.getElementById('receipts-list');

const TOKEN_KEY = 'chatter_session_token';
const DEVICE_ID_KEY = 'chatter_push_device_id';



// ==================== Password Recovery Engine Bindings ====================
const linkGotoForgot = document.getElementById('link-goto-forgot');
const forgotPasswordForm = document.getElementById('forgot-password-form');
const forgotBackButton = document.getElementById('forgot-back-button');
const forgotSubmitButton = document.getElementById('forgot-submit-button');
const forgotUsernameInput = document.getElementById('forgot-username');
const forgotEmailInput = document.getElementById('forgot-email');



let username = null;
let contactItems = [];
let onlineContacts = [];
let messages = [];
let selectedContact = null;
let selectedContactIsGroup = false;
let pendingMessage = null;
let lastRequestedContact = null;
let lastRequestedGroup = null;
let hasMoreMessages = false;
let loadingMoreMessages = false;
let loadMoreTimer = null;
let unreadCounts = {};
let recentlyOpenedChats = {};
let pendingAddedContacts = new Set();
let currentGroupIsAdmin = false;
let currentGroupAdmins = [];	
let currentGroupMembers = [];
let replyingToMessage = null;
let pendingReplyJumpMessageId = null;
let loadingReplyTarget = false;
let pendingAttachmentFile = null;
let loadingOlderForReplyJump = false;
let contactsLoading = false;
let isTyping = false;
let typingTimeout = null;
let typingUsers = new Set();


function resetOptionsMenu(menu) {
    menu.classList.add('hidden');
    menu.style.position = '';
    menu.style.left = '';
    menu.style.top = '';
    menu.style.right = '';
    menu.style.bottom = '';
}

function closeAllOptionsMenus() {
    document.querySelectorAll('.contact-options-menu').forEach((menu) => {
        resetOptionsMenu(menu);
    });
}

function positionOptionsMenu(button, menu) {
    closeAllOptionsMenus();

    menu.classList.remove('hidden');

    const margin = 8;
    const buttonRect = button.getBoundingClientRect();
    const isMobile = window.innerWidth <= 768;

    menu.style.position = 'fixed';
    menu.style.left = '0px';
    menu.style.top = '0px';
    menu.style.right = 'auto';
    menu.style.bottom = 'auto';
    menu.style.zIndex = '3000';

    requestAnimationFrame(() => {
        const menuRect = menu.getBoundingClientRect();

        let left;

        if (isMobile) {
            left = (window.innerWidth - menuRect.width) / 2;
        } else {
            left = buttonRect.right - menuRect.width;
        }

        left = Math.max(margin, left);
        left = Math.min(left, window.innerWidth - menuRect.width - margin);

        let top = buttonRect.bottom + margin;

        if (top + menuRect.height > window.innerHeight - margin) {
            top = buttonRect.top - menuRect.height - margin;
        }

        top = Math.max(margin, top);

        menu.style.left = `${left}px`;
        menu.style.top = `${top}px`;
    });
}



function addLocalSendingMessage(content, type = 'text', extra = {}) {
    const tempId = `temp-${Date.now()}-${Math.random().toString(16).slice(2)}`;

    messages.push({
        id: tempId,
        sender_username: username,
        content: content || '',
        type,
        timestamp: new Date().toISOString(),
        sending: true,
        ...extra
    });

    renderMessages();

    return tempId;
}

fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    if (!file || !selectedContact) return;

    pendingAttachmentFile = file;
    renderAttachmentPreview();

    fileInput.value = '';
});

function renderAttachmentPreview() {
    attachmentPreviewContent.innerHTML = '';

    if (!pendingAttachmentFile) {
        attachmentPreview.classList.add('hidden');
        return;
    }

    const file = pendingAttachmentFile;
    const fileType = file.type || '';

    if (fileType.startsWith('image/')) {
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.style.maxWidth = '160px';
        img.style.maxHeight = '120px';
        img.style.borderRadius = '8px';
        attachmentPreviewContent.appendChild(img);
    } else if (fileType.startsWith('video/')) {
        const video = document.createElement('video');
        video.src = URL.createObjectURL(file);
        video.controls = true;
        video.style.maxWidth = '180px';
        video.style.maxHeight = '130px';
        video.style.borderRadius = '8px';
        attachmentPreviewContent.appendChild(video);
    } else {
        const fileLabel = document.createElement('div');
        fileLabel.textContent = file.name;
        attachmentPreviewContent.appendChild(fileLabel);
    }

    attachmentPreview.classList.remove('hidden');
}

attachmentPreviewCancel.addEventListener('click', () => {
    pendingAttachmentFile = null;
	attachmentPreviewContent.innerHTML = '';
    renderAttachmentPreview();
});
function jumpToMessageById(messageId) {
    const original = document.querySelector(`[data-message-id="${messageId}"]`);

    if (!original) return false;

    original.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });

    original.classList.add('message-highlight');

    setTimeout(() => {
        original.classList.remove('message-highlight');
    }, 1200);

    return true;
}

function loadOlderUntilMessageFound(messageId) {
    if (loadingReplyTarget) return;

    if (jumpToMessageById(messageId)) {
        return;
    }

    if (!hasMoreMessages || !messages.length) {
        setMainStatus('Original message is not loaded or no longer available.', 'error');
        return;
    }

    pendingReplyJumpMessageId = messageId;
    loadingReplyTarget = true;

    setMainStatus('Loading old messages...', 'info');

    const oldestTimestamp = messages[0]?.timestamp;

    if (!oldestTimestamp) {
        loadingReplyTarget = false;
        pendingReplyJumpMessageId = null;
        return;
    }
	
	loadingOlderForReplyJump = true;
    requestConversation(oldestTimestamp);
}

if (linkGotoForgot) {
    linkGotoForgot.addEventListener('click', (e) => {
        e.preventDefault();
        if (loginForm) loginForm.classList.add('hidden');
        if (registerForm) registerForm.classList.remove('active');
        if (forgotPasswordForm) forgotPasswordForm.style.display = 'block';
        setAuthStatus('');
    });
}


if (forgotBackButton) {
    forgotBackButton.addEventListener('click', () => {
        if (forgotPasswordForm) forgotPasswordForm.classList.add('hidden');
        if (loginForm) loginForm.classList.remove('hidden');
        setAuthStatus('');
    });
}

if (forgotSubmitButton) {
    forgotSubmitButton.addEventListener('click', async () => {
        const targetUser = forgotUsernameInput.value.trim();

        if (!targetUser) {
            setAuthStatus('Please specify your username.', 'error');
            return;
        }

        setAuthStatus('Checking account status...', 'info');

        try {
            const response = await fetch('/api/forgot-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: targetUser }) // Only pass the username
            });
            const result = await response.json();

            if (response.ok && result.success) {
                setAuthStatus(result.message, 'success');
                forgotUsernameInput.value = '';
            } else {
                setAuthStatus(result.message || 'Operation failed.', 'error');
            }
        } catch (error) {
            console.error('Password reset endpoint structural failure:', error);
            setAuthStatus('Network exception occurred connecting to password API.', 'error');
        }
    });
}



function renderReplyPreview() {
    if (!replyingToMessage) {
        replyPreview.classList.add('hidden');
        replyPreviewSender.textContent = '';
        replyPreviewText.textContent = '';
        return;
    }

    replyPreviewSender.textContent = `Replying to ${replyingToMessage.sender_username}`;
    replyPreviewText.textContent = replyingToMessage.preview;
    replyPreview.classList.remove('hidden');
}

replyPreviewCancel.addEventListener('click', () => {
    replyingToMessage = null;
    renderReplyPreview();
});


function openEditMessageModal(msg) {
    editingMessage = msg;
    editMessageInput.value = msg.content || '';
    setPanelStatus(editMessageStatus, '', 'info');
    editMessageModal.classList.remove('hidden');
}

function closeEditMessageModal() {
    editMessageModal.classList.add('hidden');
    editingMessage = null;
    editMessageInput.value = '';
    setPanelStatus(editMessageStatus, '', 'info');
}

editMessageSave.addEventListener('click', () => {
    const newContent = editMessageInput.value.trim();

    if (!editingMessage || !newContent) {
        setPanelStatus(editMessageStatus, 'Message cannot be empty.', 'error');
        return;
    }

    secureEmit('edit_message', {
        chat_type: selectedContactIsGroup ? 'group' : 'contact',
        chat_name: selectedContact,
        message_id: editingMessage.id,
        content: newContent
    });

    closeEditMessageModal();
});

editMessageCancel.addEventListener('click', closeEditMessageModal);
editMessageClose.addEventListener('click', closeEditMessageModal);

editMessageModal.addEventListener('click', (event) => {
    if (event.target === editMessageModal) {
        closeEditMessageModal();
    }
});
function openVideoModal(url) {
    videoViewer.src = url;
    videoModal.classList.remove('hidden');
    videoViewer.play().catch(() => {});
}

function closeVideoModal() {
    videoViewer.pause();
    videoViewer.src = '';
    videoModal.classList.add('hidden');
}
videoClose.addEventListener('click', closeVideoModal);

videoModal.addEventListener('click', (event) => {
    if (event.target === videoModal) {
        closeVideoModal();
    }
});

// --- App Badging API Sync Helper ---
function syncNativeNotificationBadge() {
    if ('setAppBadge' in navigator) {
        const totalUnread = Object.values(unreadCounts).reduce((sum, count) => sum + (count || 0), 0);
        
        if (totalUnread > 0) {
            navigator.setAppBadge(totalUnread).catch((err) => {
                console.error("Failed to update native badge:", err);
            });
        } else {
            navigator.clearAppBadge().catch((err) => {
                console.error("Failed to clear native badge:", err);
            });

            
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.ready.then((registration) => {
                    registration.getNotifications().then((notifications) => {
                        notifications.forEach((notification) => {
                            // Close either all notifications or match your tag group specifically
                            if (notification.tag === 'chatter-chat-sync') {
                                notification.close();
                            }
                        });
                    });
                });
            }
            // -----------------------------
        }
    }
}

function renderGroupAddContactList() {
    groupAddContactList.innerHTML = '';

    const contacts = contactItems.filter((item) => {
		return item.type === 'contact' && !currentGroupMembers.includes(item.name);
	});

    contacts.forEach((contact) => {
        const row = document.createElement('label');
        row.className = 'group-member-item';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = contact.name;

        const label = document.createElement('span');
        label.textContent = contact.name;

        row.appendChild(checkbox);
        row.appendChild(label);
        groupAddContactList.appendChild(row);
    });
}

function openConfirmModal(title, message, onConfirm) {
    confirmTitle.textContent = title;
    confirmMessage.textContent = message;
    pendingConfirmAction = onConfirm;
    confirmModal.classList.remove('hidden');
}

function closeConfirmModal() {
    confirmModal.classList.add('hidden');
    pendingConfirmAction = null;
}

confirmYes.addEventListener('click', () => {
    if (pendingConfirmAction) {
        pendingConfirmAction();
    }
    closeConfirmModal();
});

confirmNo.addEventListener('click', closeConfirmModal);
confirmClose.addEventListener('click', closeConfirmModal);

confirmModal.addEventListener('click', (event) => {
    if (event.target === confirmModal) {
        closeConfirmModal();
    }
});

function isUserInContacts(memberName) {
    return contactItems.some((item) => {
        return item.type === 'contact' && item.name === memberName;
    });
}
function setPanelStatus(element, message, type = 'info') {
    if (!element) return;

    element.textContent = message;
    element.className = `status ${type}`;

    if (!message) {
        element.classList.add('hidden');
    } else {
        element.classList.remove('hidden');
    }
}
function clearUnreadCountFor(name, type) {
    const countKey = `${name}_${type}`;
    unreadCounts[countKey] = 0;
    recentlyOpenedChats[countKey] = Date.now();
    updateContactList();
	syncNativeNotificationBadge();
}
function initLoadMoreControl() {
    if (!messageList) return;
    loadMoreWrapper = document.createElement('div');
    loadMoreWrapper.id = 'load-more-wrapper';
    loadMoreWrapper.className = 'load-more-wrapper hidden';
    loadMoreButton = document.createElement('button');
    loadMoreButton.id = 'load-more-button';
    loadMoreButton.className = 'load-more-button';
    loadMoreButton.type = 'button';
    loadMoreButton.textContent = 'Load more messages';
    loadMoreButton.addEventListener('click', loadMoreMessages);
    loadMoreWrapper.appendChild(loadMoreButton);
    messageList.addEventListener('scroll', updateLoadMoreButton);
}

function isMessageNew(msg) {
    if (msg.sender_username === username) return false;
    if (msg.read === false || msg.is_read === false) return true;
    if (msg.read_by && msg.read_by[username] === false) return true;
    return false;
}

function secureEmit(event, data) {
    const token = localStorage.getItem(TOKEN_KEY);
    socket.emit(event, { ...data, token });
}

function getCurrentTypingPayload() {
    if (!username || !selectedContact) return null;

    return {
        chat_type: selectedContactIsGroup ? 'group' : 'contact',
        chat_name: selectedContact
    };
}

function startTyping() {
    const payload = getCurrentTypingPayload();
    if (!payload) return;

    if (!isTyping) {
        isTyping = true;
        secureEmit('typing_start', payload);
    }

    clearTimeout(typingTimeout);

    typingTimeout = setTimeout(() => {
        stopTyping();
    }, 2000);
}

function stopTyping() {
    const payload = getCurrentTypingPayload();

    clearTimeout(typingTimeout);
    typingTimeout = null;

    if (!isTyping) return;

    isTyping = false;

    if (payload) {
        secureEmit('typing_stop', payload);
    }
}

function clearTypingDisplay() {
    typingUsers.clear();
    renderTypingIndicator();
}

function renderTypingIndicator() {
    let indicator = document.getElementById('typing-indicator');

    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'typing-indicator';
        indicator.className = 'typing-indicator';

        if (messageList) {
            messageList.insertAdjacentElement('afterend', indicator);
        }
    }

    const users = Array.from(typingUsers);

    if (!users.length) {
        indicator.classList.add('hidden');
        indicator.textContent = '';
        return;
    }

    if (users.length === 1) {
        indicator.textContent = `${users[0]} is typing...`;
    } else if (users.length === 2) {
        indicator.textContent = `${users[0]} and ${users[1]} are typing...`;
    } else {
        indicator.textContent = `${users.length} people are typing...`;
    }

    indicator.classList.remove('hidden');
}

function saveToken(token) {
    if (token) {
        localStorage.setItem(TOKEN_KEY, token); // Changed to localStorage
    }
}

function clearTokenStore() {
    localStorage.removeItem(TOKEN_KEY); // Changed to localStorage
}

// Brand new function to check for a token on startup
function checkPersistentToken() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
		if (appLoadingScreen) appLoadingScreen.classList.remove('hidden');
        secureEmit('token_login', {}); // Ask server to verify token
        return true;
    }
    return false;
}

function setThemeMode(mode) {
    const lightMode = mode === 'light';
    document.body.classList.toggle('dark-mode', !lightMode);
	document.documentElement.classList.toggle('dark-mode', !lightMode);
    
    let metaTheme = document.querySelector('meta[name="theme-color"]');
    if (!metaTheme) {
        metaTheme = document.createElement('meta');
        metaTheme.setAttribute('name', 'theme-color');
        document.head.appendChild(metaTheme);
    }
    metaTheme.setAttribute('content', lightMode ? '#f3f6fb' : '#121827');
    // -------------------------------------------------------------------

    if (themeToggleButton) {
        themeToggleButton.classList.toggle('dark', !lightMode);
        themeToggleButton.setAttribute('aria-pressed', (!lightMode).toString());
        themeToggleButton.title = lightMode ? 'Switch to dark mode' : 'Switch to light mode';
    }
    if (themeModeText) {
        themeModeText.textContent = lightMode ? 'Light mode' : 'Dark mode';
    }
    localStorage.setItem('chatter_theme_mode', lightMode ? 'light' : 'dark');
}

function initializeTheme() {
    const storedMode = localStorage.getItem('chatter_theme_mode') || 'light';
    setThemeMode(storedMode);
}

// Toggle the toolbar dropdown menu
function toggleToolbarMenu(show) {
    if (!toolbarMenu || !toolbarActionButton) return;
    const isHidden = toolbarMenu.classList.contains('hidden');
    const shouldShow = typeof show === 'boolean' ? show : isHidden;
    toolbarMenu.classList.toggle('hidden', !shouldShow);
    toolbarActionButton.setAttribute('aria-expanded', shouldShow.toString());
}

function applyImageZoom() {
    imageViewerImg.style.transform = `scale(${imageZoomLevel})`;
}

function openImageModal(url, fileName) {
	currentImageUrl = url;
	currentImageName = fileName || 'image';
    imageZoomLevel = 1;
    imageViewerImg.src = url;
    applyImageZoom();
    imageModal.classList.remove('hidden');
}

function closeImageModal() {
    imageModal.classList.add('hidden');
    imageViewerImg.src = '';
    imageZoomLevel = 1;
}
function isIOSDevice() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent)
        || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
}
imageClose.addEventListener('click', closeImageModal);

imageZoomIn.addEventListener('click', () => {
    imageZoomLevel = Math.min(imageZoomLevel + 0.25, 5);
    applyImageZoom();
});

imageZoomOut.addEventListener('click', () => {
    imageZoomLevel = Math.max(imageZoomLevel - 0.25, 0.5);
    applyImageZoom();
});

imageModal.addEventListener('click', (event) => {
    if (event.target === imageModal) {
        closeImageModal();
    }
});
imageSave.addEventListener('click', async () => {
    if (!isIOSDevice()) {
        const link = document.createElement('a');
        link.href = currentImageUrl;
        link.download = currentImageName || 'image';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        return;
    }

    try {
        const response = await fetch(currentImageUrl);
        const blob = await response.blob();
        const file = new File([blob], currentImageName || 'image', { type: blob.type });

        if (navigator.canShare && navigator.canShare({ files: [file] })) {
            await navigator.share({
                files: [file],
                title: currentImageName || 'image'
            });
        } else {
            window.open(currentImageUrl, '_blank');
        }
    } catch (err) {
        console.error('Save/share failed:', err);
        window.open(currentImageUrl, '_blank');
    }
});

imageViewerImg.addEventListener('wheel', (event) => {
    event.preventDefault();

    if (event.deltaY < 0) {
        imageZoomLevel = Math.min(imageZoomLevel + 0.1, 5);
    } else {
        imageZoomLevel = Math.max(imageZoomLevel - 0.1, 0.5);
    }

    applyImageZoom();
});
// Close menu on any outside click or Escape
document.addEventListener('click', (e) => {
    if (!toolbarMenu || !toolbarActionButton) return;
    if (toolbarMenu.classList.contains('hidden')) return;
    if (e.target === toolbarActionButton || toolbarMenu.contains(e.target)) return;
    toggleToolbarMenu(false);
});
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') toggleToolbarMenu(false);
});

if (toolbarActionButton) {
    toolbarActionButton.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleToolbarMenu();
    });
}

if (addContactButton) {
    addContactButton.addEventListener('click', (e) => {
        // keep normal behavior but close the menu
        toggleToolbarMenu(false);
        addContact();
    });
}

if (createGroupButton) {
    createGroupButton.addEventListener('click', (e) => {
        toggleToolbarMenu(false);
        openGroupCreator();
    });
}
function getRequestedChatFromUrl() {
    const params = new URLSearchParams(window.location.search);
    const chat = params.get('chat');
    const type = params.get('type');

    if (!chat || !type) return null;

    return {
        name: chat,
        type: type
    };
}
function toggleThemeMode() {
    const currentMode = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
    setThemeMode(currentMode === 'light' ? 'dark' : 'light');
}

function showScreen(screenId) {
    if (authScreen) {
        authScreen.classList.toggle('hidden', screenId !== 'auth-screen');
    }
    if (mainScreen) {
        mainScreen.classList.toggle('hidden', screenId !== 'main-screen');
    }
    document.body.classList.toggle('main-visible', screenId === 'main-screen');
}

function setAuthStatus(message, type = 'info') {
	if (!authStatus) {
        // If we're on the main chat page, log it to console or direct it to mainStatus instead
        if (message) console.log(`[Auth Log Context]: ${message}`);
        return;
    }
    authStatus.textContent = message;
    authStatus.className = `status ${type}`;
}

function setMainStatus(message, type = 'info') {
    if (message) console.log(`[main-status] ${type}: ${message}`);
}

function updateComposerState() {
    const showComposer = !!selectedContact;
    if (composer) {
        composer.classList.toggle('hidden', !showComposer);
    }
    messageInput.disabled = !showComposer;
    sendButton.disabled = !showComposer;
    if (!showComposer) {
        messageInput.value = '';
    }
}

function switchTab(tab) {
    tabLogin.classList.toggle('active', tab === 'login');
    tabRegister.classList.toggle('active', tab === 'register');
    loginForm.classList.toggle('active', tab === 'login');
    registerForm.classList.toggle('active', tab === 'register');
    setAuthStatus('');
}

function updateContactList() {
    contactList.innerHTML = '';
	if (contactsLoading) {
        const loading = document.createElement('li');
        loading.className = 'contact-item';
        loading.textContent = 'Loading contacts...';
        contactList.appendChild(loading);
        return;
    }
    if (!contactItems.length) {
        const empty = document.createElement('li');
        empty.textContent = 'No contacts or groups yet. Add a contact to start chatting.';
        empty.className = 'contact-item';
        contactList.appendChild(empty);
        return;
    }
    contactItems.forEach((item) => {
        const listItem = document.createElement('li');
        listItem.className = 'contact-item';
        listItem.dataset.name = item.name;
        listItem.dataset.type = item.type;
        if (selectedContact === item.name && selectedContactIsGroup === (item.type === 'group')) {
            listItem.classList.add('active');
        }
        const label = document.createElement('span');
        const countKey = `${item.name}_${item.type}`;
        const count = unreadCounts[countKey] || 0;
        let labelText = item.display;
        if (count > 0) {
            labelText += ` (${count})`;
        }
        label.textContent = labelText;
        const status = document.createElement('span');
        status.className = 'type';
        status.textContent = item.removed
			? 'Removed'
			: item.type === 'group'
				? 'group'
				: onlineContacts.includes(item.name) ? 'online' : 'offline';
		const optionsWrapper = document.createElement('div');
		optionsWrapper.style.position = 'relative';

		const optionsButton = document.createElement('button');
		optionsButton.type = 'button';
		optionsButton.textContent = '⋯';
		optionsButton.className = 'contact-options-button';

		const optionsMenu = document.createElement('div');
		optionsMenu.className = 'contact-options-menu hidden';

		if (item.removed) {
			const deleteRemovedBtn = document.createElement('button');
			deleteRemovedBtn.type = 'button';
			deleteRemovedBtn.textContent = 'Delete chat';
			deleteRemovedBtn.className = 'contact-options-menu-item danger';

			deleteRemovedBtn.addEventListener('click', (event) => {
				event.stopPropagation();
				resetOptionsMenu(optionsMenu);
				openConfirmModal(
					'Delete removed group?',
					'Are you sure you want to delete this removed group from your chat list?',
					() => {
						secureEmit('delete_removed_group', {
							group_name: item.name
						});
					}
				);
			});

			optionsMenu.appendChild(deleteRemovedBtn);
		} else {
			const deleteConversationBtn = document.createElement('button');
			deleteConversationBtn.type = 'button';
			deleteConversationBtn.textContent = 'Delete conversation';
			deleteConversationBtn.className = 'contact-options-menu-item';

			deleteConversationBtn.addEventListener('click', (event) => {
				event.stopPropagation();
				resetOptionsMenu(optionsMenu);

				openConfirmModal(
					'Delete conversation?',
					item.type === 'group'
						? 'Are you sure you want to delete this group conversation? Doing so will erase the conversation for all group members.'
						: 'Are you sure you want to delete this conversation? Doing so will erase the conversation for both users.',
					() => {
						secureEmit('delete_conversation', {
							target_name: item.name,
							target_type: item.type
						});
					}
				);
			});

			optionsMenu.appendChild(deleteConversationBtn);

			if (item.type === 'contact') {
				const removeContactBtn = document.createElement('button');
				removeContactBtn.type = 'button';
				removeContactBtn.textContent = 'Remove contact';
				removeContactBtn.className = 'contact-options-menu-item danger';

				removeContactBtn.addEventListener('click', (event) => {
					event.stopPropagation();
					resetOptionsMenu(optionsMenu);

					openConfirmModal(
						'Remove contact?',
						'Are you sure you want to delete this contact? Doing so will erase your existing conversation.',
						() => {
							secureEmit('remove_contact', {
								contact_username: item.name
							});
						}
					);
				});

				optionsMenu.appendChild(removeContactBtn);
			}

			if (item.type === 'group') {
				const isAdminForThisGroup = item.is_admin === true;

				if (isAdminForThisGroup) {
					const deleteGroupBtn = document.createElement('button');
					deleteGroupBtn.type = 'button';
					deleteGroupBtn.textContent = 'Delete group chat';
					deleteGroupBtn.className = 'contact-options-menu-item danger';

					deleteGroupBtn.addEventListener('click', (event) => {
						event.stopPropagation();
						resetOptionsMenu(optionsMenu);

						openConfirmModal(
							'Delete group chat?',
							'Are you sure you want to delete this group chat? This will erase it for all members.',
							() => {
								secureEmit('delete_group_chat', {
									group_name: item.name
								});
							}
						);
					});

					optionsMenu.appendChild(deleteGroupBtn);
				}
			}
		}

		

		optionsButton.addEventListener('click', (event) => {
			event.stopPropagation();

			if (optionsMenu.classList.contains('hidden')) {
				positionOptionsMenu(optionsButton, optionsMenu);
			} else {
				resetOptionsMenu(optionsMenu);
			}
		});

		optionsWrapper.appendChild(optionsButton);
		optionsWrapper.appendChild(optionsMenu);
        const rightSide = document.createElement('div');
		rightSide.style.display = 'flex';
		rightSide.style.alignItems = 'center';
		rightSide.style.gap = '8px';

		rightSide.appendChild(status);
		rightSide.appendChild(optionsWrapper);

		listItem.appendChild(label);
		listItem.appendChild(rightSide);
        contactList.appendChild(listItem);
    });
}
function openSettingsModal() {
    membersModal.classList.add('hidden');
    receiptsModal.classList.add('hidden');
    settingsStatus.textContent = '';
    settingsStatus.className = 'status';
    
    passwordChangeForm.classList.add('hidden');
    settingsMenuOptions.classList.remove('hidden'); 
    settingsModal.classList.remove('hidden');
    
    // Request current email from server to pre-fill the input field
    //secureEmit('get_current_recovery_email', { username });
}



function closeSettingsModal() {
    settingsModal.classList.add('hidden');
    currentPassInput.value = '';
    newPassInput.value = '';
}
function openReceiptsModal(readByMap) {
    // 1. Force the members modal to vanish completely so it can't trap clicks or overlap
    membersModal.classList.add('hidden');
    
    receiptsList.innerHTML = '';
    if (!readByMap || Object.keys(readByMap).length === 0) {
        const empty = document.createElement('div');
        empty.className = 'member-item';
        empty.textContent = 'No other members tracking receipt metadata.';
        receiptsList.appendChild(empty);
    } else {
        for (const [user, hasRead] of Object.entries(readByMap)) {
            const row = document.createElement('div');
            row.className = 'member-item';
            row.textContent = `${user}: ${hasRead ? 'Read' : 'Unread'}`;
            receiptsList.appendChild(row);
        }
    }
    // 2. Un-hide the receipts tracking panel layout safely
    receiptsModal.classList.remove('hidden');
}

function formatTimestamp(timestamp) {
    if (!timestamp) return '';
    const parsed = new Date(timestamp);
    if (Number.isNaN(parsed.getTime())) return String(timestamp);

    const pad = (value) => String(value).padStart(2, '0');
    const hours = pad(parsed.getHours());
    const minutes = pad(parsed.getMinutes());
    const month = pad(parsed.getMonth() + 1);
    const day = pad(parsed.getDate());
    const now = new Date();

    if (parsed.getFullYear() === now.getFullYear()) {
        return `${hours}:${minutes} ${month}/${day}`;
    }
    return `${hours}:${minutes} ${parsed.getFullYear()}/${month}/${day}`;
}

function getMessagePreview(msg) {
    if (!msg) return '';

    if (msg.deleted) return 'This message was deleted';
    if (msg.type === 'image') return 'Image';
    if (msg.type === 'video') return 'Video';
    if (msg.type === 'file') return msg.file_name || 'File';

    return msg.content || '';
}
function appendMessageCaption(container, msg) {
    if (!msg.content || !msg.content.trim()) return;

    const caption = document.createElement('div');
    caption.className = 'message-caption';
    caption.textContent = msg.content;
    caption.style.marginTop = '8px';

    container.appendChild(caption);
}
function startReplyToMessage(msg) {
    replyingToMessage = {
        id: msg.id,
        sender_username: msg.sender_username,
        type: msg.type,
        preview: getMessagePreview(msg)
    };

    renderReplyPreview();
    messageInput.focus();
}

function getAuthenticatedFileUrl(url) {
    const token = localStorage.getItem(TOKEN_KEY);

    if (!token) return url;

    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}token=${encodeURIComponent(token)}`;
}

async function openPdfModal(url, fileName = 'PDF Viewer') {
    pdfModal.classList.remove('hidden');
    pdfTitle.textContent = fileName;

    pdfDoc = null;
    pdfPageNumber = 1;
    pdfScale = window.innerWidth <= 768 ? 0.9 : 1.2;

    pdfPageInfo.textContent = 'Loading...';
    pdfZoomLabel.textContent = `${Math.round(pdfScale * 100)}%`;

    const fullUrl = getAuthenticatedFileUrl(url);

    try {
        pdfjsLib.GlobalWorkerOptions.workerSrc =
            'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

        pdfDoc = await pdfjsLib.getDocument(fullUrl).promise;
        renderPdfPage(pdfPageNumber);
    } catch (err) {
        console.error('PDF load failed:', err);
        pdfPageInfo.textContent = 'Could not load PDF.';
    }
}

function renderPdfPage(pageNumber) {
    if (!pdfDoc || pdfRendering) {
        pdfPendingPage = pageNumber;
        return;
    }

    pdfRendering = true;

    pdfDoc.getPage(pageNumber).then((page) => {
        const viewport = page.getViewport({ scale: pdfScale });
        const context = pdfCanvas.getContext('2d');

        pdfCanvas.width = viewport.width;
        pdfCanvas.height = viewport.height;

        const renderContext = {
            canvasContext: context,
            viewport
        };

        const renderTask = page.render(renderContext);

        renderTask.promise.then(() => {
            pdfRendering = false;

            pdfPageInfo.textContent = `Page ${pdfPageNumber} / ${pdfDoc.numPages}`;
            pdfZoomLabel.textContent = `${Math.round(pdfScale * 100)}%`;

            if (pdfPendingPage !== null) {
                const pending = pdfPendingPage;
                pdfPendingPage = null;
                renderPdfPage(pending);
            }
        });
    });
}

function closePdfModal() {
    pdfModal.classList.add('hidden');

    pdfDoc = null;
    pdfPageNumber = 1;
    pdfPendingPage = null;
    pdfRendering = false;

    const context = pdfCanvas.getContext('2d');
    context.clearRect(0, 0, pdfCanvas.width, pdfCanvas.height);
}

pdfClose.addEventListener('click', closePdfModal);

pdfPrev.addEventListener('click', () => {
    if (!pdfDoc || pdfPageNumber <= 1) return;

    pdfPageNumber -= 1;
    renderPdfPage(pdfPageNumber);
});

pdfNext.addEventListener('click', () => {
    if (!pdfDoc || pdfPageNumber >= pdfDoc.numPages) return;

    pdfPageNumber += 1;
    renderPdfPage(pdfPageNumber);
});

pdfZoomIn.addEventListener('click', () => {
    if (!pdfDoc) return;

    pdfScale = Math.min(pdfScale + 0.2, 3);
    renderPdfPage(pdfPageNumber);
});

pdfZoomOut.addEventListener('click', () => {
    if (!pdfDoc) return;

    pdfScale = Math.max(pdfScale - 0.2, 0.5);
    renderPdfPage(pdfPageNumber);
});

pdfModal.addEventListener('click', (event) => {
    if (event.target === pdfModal) {
        closePdfModal();
    }
});

function renderMessages(preserveScroll = false) {
    let previousScrollHeight = 0;
    let previousScrollTop = 0;
    if (preserveScroll) {
        previousScrollHeight = messageList.scrollHeight;
        previousScrollTop = messageList.scrollTop;
    }

    messageList.innerHTML = '';
    if (!loadMoreWrapper) {
        initLoadMoreControl();
    }
    if (loadMoreWrapper) {
        messageList.appendChild(loadMoreWrapper);
    }

    if (!messages.length) {
        if (!selectedContact) {
            return;
        }
        const hint = document.createElement('div');
        hint.className = 'message';
        hint.textContent = 'No messages yet.';
        messageList.appendChild(hint);
        if (preserveScroll) {
            messageList.scrollTop = previousScrollTop;
        }
        return;
    }

    const firstNewMessageIndex = messages.findIndex((msg) => {
        return isMessageNew(msg);
    });

    messages.forEach((msg, index) => {
		if (msg.type === 'system') {
			const systemEl = document.createElement('div');
			systemEl.className = 'message-separator';
			systemEl.textContent = msg.content;
			messageList.appendChild(systemEl);
			return;
		}
                if (firstNewMessageIndex > 0 && index === firstNewMessageIndex) {
                    const separator = document.createElement('div');
                    separator.className = 'message-separator';
                    separator.textContent = '--------------- New messages ---------------';
                    messageList.appendChild(separator);
                }
                const messageEl = document.createElement('div');
                messageEl.className = 'message';
				
				if (msg.id) {
					messageEl.dataset.messageId = msg.id;
				}
				let touchStartX = 0;
				let touchStartY = 0;
				let touchMoved = false;

				messageEl.addEventListener('touchstart', (event) => {
					if (!msg.id || msg.deleted) return;

					touchStartX = event.touches[0].clientX;
					touchStartY = event.touches[0].clientY;
					touchMoved = false;
				}, { passive: true });

				messageEl.addEventListener('touchmove', (event) => {
					if (!msg.id || msg.deleted) return;

					const deltaX = event.touches[0].clientX - touchStartX;
					const deltaY = event.touches[0].clientY - touchStartY;

					if (Math.abs(deltaX) > 10 || Math.abs(deltaY) > 10) {
						touchMoved = true;
					}

					if (deltaX < 0 && Math.abs(deltaX) > Math.abs(deltaY)) {
						event.preventDefault();
						messageEl.style.transform = `translateX(${Math.max(deltaX, -70)}px)`;
					}
				}, { passive: false });

				messageEl.addEventListener('touchend', (event) => {
					if (!msg.id || msg.deleted) return;

					const deltaX = event.changedTouches[0].clientX - touchStartX;
					const deltaY = event.changedTouches[0].clientY - touchStartY;

					messageEl.style.transform = '';

					if (
						touchMoved &&
						deltaX < -60 &&
						Math.abs(deltaX) > Math.abs(deltaY)
					) {
						startReplyToMessage(msg);
					}
				}, { passive: true });
                if (msg.sender_username === username) messageEl.classList.add('you');
                
                const header = document.createElement('div');
                header.className = 'message-header';
                header.textContent = msg.sender_username === username ? 'You' : msg.sender_username;
                
                const text = document.createElement('div');
				const bodyContent = document.createElement('div');

				if (msg.reply_to) {
					const replyBox = document.createElement('div');
					replyBox.className = 'message-reply-box';

					const replySender = document.createElement('div');
					replySender.className = 'message-reply-sender';
					replySender.textContent = msg.reply_to.sender_username || 'Unknown';

					const replyText = document.createElement('div');
					replyText.className = 'message-reply-text';
					replyText.textContent = msg.reply_to.preview || 'Original message';

					replyBox.appendChild(replySender);
					replyBox.appendChild(replyText);

					replyBox.addEventListener('click', () => {
						loadOlderUntilMessageFound(msg.reply_to.id);
					});

					text.appendChild(replyBox);
				}
                if (msg.type === 'image' && msg.file_url) {
					const img = document.createElement('img');
					img.src = msg.file_url;
					img.alt = msg.file_name || 'sent image';
					img.style.maxWidth = '240px';
					img.style.borderRadius = '8px';
					img.style.cursor = 'zoom-in';
					img.onload = () => {
						if (!preserveScroll) {
							messageList.scrollTop = messageList.scrollHeight;
						}
					};
					img.addEventListener('click', () => {
						openImageModal(msg.file_url, msg.file_name);
					});

					text.appendChild(img);
					appendMessageCaption(text, msg);
				} else if (msg.type === 'video' && msg.file_url) {
					const videoPreview = document.createElement('video');
					videoPreview.src = msg.file_url;
					videoPreview.controls = false;
					videoPreview.muted = true;
					videoPreview.style.maxWidth = '240px';
					videoPreview.style.borderRadius = '8px';
					videoPreview.style.cursor = 'pointer';

					videoPreview.addEventListener('click', () => {
						openVideoModal(msg.file_url);
					});

					text.appendChild(videoPreview);
					appendMessageCaption(text, msg);
				} else if (msg.type === 'file' && msg.file_url) {
					const link = document.createElement('a');

					link.href = '#';
					link.textContent = msg.file_name || 'Download file';

					link.onclick = (e) => {
						e.preventDefault();

						if (msg.file_type === 'application/pdf') {
							openPdfModal(msg.file_url, msg.file_name || 'PDF Viewer');
						} else {
							window.open(msg.file_url, '_blank');
						}
					};

					text.appendChild(link);
					appendMessageCaption(text, msg);
				} else {
					if (msg.deleted) {
						bodyContent.textContent = 'This message was deleted';
						bodyContent.style.fontStyle = 'italic';
						bodyContent.style.color = 'var(--muted)';
					} else {
						bodyContent.textContent = msg.content;
					}

					text.appendChild(bodyContent);
				}
        
        const timestamp = formatTimestamp(msg.timestamp);
        if (timestamp) {
            const timeEl = document.createElement('div');
            timeEl.className = 'message-timestamp';
            timeEl.textContent = timestamp;
            timeEl.style.fontSize = '10px';
            timeEl.style.color = 'var(--muted)';
            timeEl.style.marginTop = '4px';
            text.appendChild(timeEl);
        }
		if (msg.edited && !msg.deleted) {
			const editedEl = document.createElement('span');
			editedEl.textContent = ' edited';
			editedEl.style.fontSize = '10px';
			editedEl.style.color = 'var(--muted)';
			editedEl.style.marginLeft = '6px';
			text.appendChild(editedEl);
		}
		if (msg.sending) {
			const sendingEl = document.createElement('span');
			sendingEl.textContent = ' Sending...';
			sendingEl.style.fontSize = '10px';
			sendingEl.style.color = 'var(--muted)';
			sendingEl.style.marginLeft = '6px';
			text.appendChild(sendingEl);
		}
		if (msg.failed) {
			const failedEl = document.createElement('span');
			failedEl.textContent = ' Failed';
			failedEl.style.fontSize = '10px';
			failedEl.style.color = 'var(--danger)';
			failedEl.style.marginLeft = '6px';
			text.appendChild(failedEl);
		}
        messageEl.appendChild(header);
        messageEl.appendChild(text);
		if (!msg.deleted && msg.id  && !msg.sending) {
			const msgOptionsWrapper = document.createElement('div');
			msgOptionsWrapper.style.position = 'relative';
			msgOptionsWrapper.style.marginTop = '6px';

			const msgOptionsBtn = document.createElement('button');
			msgOptionsBtn.type = 'button';
			msgOptionsBtn.textContent = '⋯';
			msgOptionsBtn.className = 'contact-options-button';

			const msgOptionsMenu = document.createElement('div');
			msgOptionsMenu.className = 'contact-options-menu hidden';
			
			const replyBtn = document.createElement('button');
			replyBtn.type = 'button';
			replyBtn.textContent = 'Reply';
			replyBtn.className = 'contact-options-menu-item';

			replyBtn.addEventListener('click', (event) => {
				event.stopPropagation();
				resetOptionsMenu(msgOptionsMenu);
				startReplyToMessage(msg);
			});

			msgOptionsMenu.appendChild(replyBtn);
			if (msg.sender_username === username){
				if (msg.type === 'text') {
					const editBtn = document.createElement('button');
					editBtn.type = 'button';
					editBtn.textContent = 'Edit message';
					editBtn.className = 'contact-options-menu-item';

					editBtn.addEventListener('click', (event) => {
						event.stopPropagation();
						resetOptionsMenu(msgOptionsMenu);
						openEditMessageModal(msg);
					});

					msgOptionsMenu.appendChild(editBtn);
				}

				const deleteBtn = document.createElement('button');
				deleteBtn.type = 'button';
				deleteBtn.textContent = 'Delete message';
				deleteBtn.className = 'contact-options-menu-item danger';

				deleteBtn.addEventListener('click', (event) => {
					event.stopPropagation();
					resetOptionsMenu(msgOptionsMenu);
					msgOptionsMenu.style.position = '';
					msgOptionsMenu.style.left = '';
					msgOptionsMenu.style.top = '';
					msgOptionsMenu.style.bottom = '';
					msgOptionsMenu.style.right = '';
					openConfirmModal(
						'Delete message?',
						'Are you sure you want to delete this message?',
						() => {
							secureEmit('delete_message', {
								chat_type: selectedContactIsGroup ? 'group' : 'contact',
								chat_name: selectedContact,
								message_id: msg.id
							});
						}
					);
				});

				msgOptionsMenu.appendChild(deleteBtn);

			}
			
			msgOptionsBtn.addEventListener('click', (event) => {
				event.stopPropagation();

				if (msgOptionsMenu.classList.contains('hidden')) {
					positionOptionsMenu(msgOptionsBtn, msgOptionsMenu);
				} else {
					resetOptionsMenu(msgOptionsMenu);
				}
			});

			msgOptionsWrapper.appendChild(msgOptionsBtn);
			msgOptionsWrapper.appendChild(msgOptionsMenu);
			messageEl.appendChild(msgOptionsWrapper);
		}

        // --- READ RECEIPT LOGIC ---
        if (!selectedContactIsGroup) {
            if (msg.sender_username === username) {
                const checkmark = document.createElement('span');
                checkmark.style.fontSize = '12px';
                checkmark.style.color = (msg.read || msg.is_read) ? 'var(--secondary)' : 'var(--muted)';
                checkmark.style.marginLeft = '8px';
                checkmark.textContent = (msg.read || msg.is_read) ? ' (Read)' : ' (Unread)';
                text.appendChild(checkmark);
            }
        } else {
            if (msg.sender_username === username && msg.read_by) {
                const receiptBtn = document.createElement('button');
                receiptBtn.textContent = "Info";
                receiptBtn.style.fontSize = '10px';
                receiptBtn.style.padding = '2px 6px';
                receiptBtn.style.marginLeft = '10px';
                receiptBtn.style.borderRadius = '4px';
                receiptBtn.style.background = '#e2e8f0';
                receiptBtn.style.cursor = 'pointer';
                
                // Embedded Modal Popup instead of standard Alert()
                receiptBtn.onclick = () => {
                    openReceiptsModal(msg.read_by);
                };
                text.appendChild(receiptBtn);
            }
        }
        
        messageList.appendChild(messageEl);
    });
    if (preserveScroll) {
        messageList.scrollTop = Math.max(0, messageList.scrollHeight - previousScrollHeight + previousScrollTop);
    } else {
        messageList.scrollTop = messageList.scrollHeight;
    }
    updateLoadMoreButton();
}
document.addEventListener('pointerdown', (event) => {
    if (
        event.target.closest('.contact-options-menu') ||
        event.target.closest('.contact-options-button')
    ) {
        return;
    }

    closeAllOptionsMenus();
});
function buildContactItems(contacts, groups) {
    contactItems = [];
    contacts.forEach((contact) => {
        contactItems.push({ name: contact, display: contact, type: 'contact' });
    });
    groups.forEach((groupName) => {
        contactItems.push({ name: groupName, display: groupName, type: 'group' });
    });
    updateContactList();
    // request unread counts for all contacts
    contacts.forEach((contact) => {
        secureEmit('get_unread_messages_count', { username, contact_username: contact });
    });
    groups.forEach((groupName) => {
        secureEmit('get_unread_group_messages_count', { username, group_name: groupName });
    });
}

function startMainScreen() {
    usernameDisplay.textContent = username;
    currentUserPanel.classList.remove('hidden');
    showScreen('main-screen');
	
	contactsLoading = true;
    updateContactList();
	
    setMainStatus('Connected. Fetching contacts...', 'info');
    secureEmit('set_online_status', { username, status: true });
    secureEmit('get_contacts', { username });
	
	const requestedChat = getRequestedChatFromUrl();

	if (requestedChat) {
		window.pendingNotificationChat = requestedChat;
	}
    updateComposerState();
}

function clearSession() {
    clearTokenStore(); 
    username = null;
    contactItems = [];
    onlineContacts = [];
    messages = [];
    selectedContact = null;
    selectedContactIsGroup = false;
    pendingMessage = null;
    unreadCounts = {}; 
    buildContactItems([], []);
    renderMessages();
    updateComposerState();
    contactsLoading = false;
    if ('clearAppBadge' in navigator) {
        navigator.clearAppBadge().catch(err => console.error(err));
    }
}

function resetAuthForm() {
    if (loginForm) loginForm.reset();
    if (registerForm) registerForm.reset();
    setAuthStatus('');
}

function requestConversation(cursorTimestamp = null) {
    if (!selectedContact) return;
    const payload = { username };
    if (cursorTimestamp) payload.cursor_timestamp = cursorTimestamp;
    console.log('requestConversation', { selectedContact, selectedContactIsGroup, cursorTimestamp, payload });
    if (selectedContactIsGroup) {
        lastRequestedGroup = selectedContact;
        lastRequestedContact = null;
        secureEmit('get_group_conversation', { ...payload, group_name: selectedContact });
    } else {
        lastRequestedContact = selectedContact;
        lastRequestedGroup = null;
        secureEmit('get_conversation', { ...payload, contact_username: selectedContact });
    }
}

function clearLoadMoreTimer() {
    if (loadMoreTimer) {
        clearTimeout(loadMoreTimer);
        loadMoreTimer = null;
    }
}

function loadMoreMessages() {
    if (!selectedContact || !messages.length || loadingMoreMessages) return;
    const oldestTimestamp = messages[0]?.timestamp;
    if (!oldestTimestamp) return;
    console.log('loadMoreMessages clicked', { selectedContact, selectedContactIsGroup, oldestTimestamp });
    loadingMoreMessages = true;
    updateLoadMoreButton();
    setMainStatus('Loading older messages...', 'info');
    clearLoadMoreTimer();
    loadMoreTimer = window.setTimeout(() => {
        loadingMoreMessages = false;
        loadMoreTimer = null;
        updateLoadMoreButton();
        setMainStatus('Load more request timed out. Please try again.', 'error');
    }, 10000);
    requestConversation(oldestTimestamp);
}

function updateLoadMoreButton() {
    if (!loadMoreButton || !messageList) return;
    const atTop = messageList.scrollTop <= 4;
    const shouldShow = hasMoreMessages && selectedContact && atTop;
    loadMoreButton.classList.toggle('hidden', !shouldShow);
    loadMoreWrapper?.classList.toggle('hidden', !shouldShow);
    loadMoreButton.disabled = loadingMoreMessages;
    loadMoreButton.textContent = loadingMoreMessages ? 'Loading...' : 'Load more messages';
}
function markLocalMessageFailed(tempMessageId, errorMessage) {
    messages = messages.map((msg) => {
        if (msg.id !== tempMessageId) return msg;

        return {
            ...msg,
            sending: false,
            failed: true,
            content: errorMessage || 'Failed to send'
        };
    });

    renderMessages();
}
async function sendPendingAttachment(content, replyToPayload) {
    const file = pendingAttachmentFile;
    if (!file || !selectedContact) return;
	const fileType = file.type || '';
	const isLocalImage = fileType.startsWith('image/');
	const isLocalVideo = fileType.startsWith('video/');

	let localUrl = null;

	if (isLocalImage || isLocalVideo) {
		localUrl = URL.createObjectURL(file);
	}

	const tempMessageId = addLocalSendingMessage(content || file.name, isLocalImage ? 'image' : isLocalVideo ? 'video' : 'file', {
		file_url: localUrl,
		file_name: file.name,
		file_type: file.type,
		reply_to: replyToPayload
	});
    pendingAttachmentFile = null;
    renderAttachmentPreview();

    replyingToMessage = null;
    renderReplyPreview();

    const formData = new FormData();
    formData.append('file', file);
    formData.append('token', localStorage.getItem(TOKEN_KEY));

    const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
         markLocalMessageFailed(
			tempMessageId,
			response.status === 413
				? 'Failed to send: file is too large.'
				: `Failed to send: upload error ${response.status}.`
		);
		return;
    }

    const result = await response.json();

    if (!result.success) {
		markLocalMessageFailed(tempMessageId, result.message || 'Failed to send.');
		return;
	}

    const isImage = result.file_type && result.file_type.startsWith('image/');
    const isVideo = result.file_type && result.file_type.startsWith('video/');

    const messagePayload = {
        sender_username: username,
        content: content || '',
        type: isImage ? 'image' : isVideo ? 'video' : 'file',
        file_url: result.file_url,
        file_name: result.file_name,
        file_type: result.file_type,
        reply_to: replyToPayload
    };

    if (selectedContactIsGroup) {
        secureEmit('send_group_message', {
            ...messagePayload,
            group_name: selectedContact
        });
    } else {
        secureEmit('send_message', {
            ...messagePayload,
            receiver_username: selectedContact
        });
    }

    messageInput.value = '';

    setTimeout(() => {
        requestConversation();
    }, 300);
}
function sendMessage() {
	stopTyping();
    const content = messageInput.value.trim();
    const replyToPayload = replyingToMessage ? { ...replyingToMessage } : null;

    if (!selectedContact) {
        setMainStatus('Please choose a contact or group first.', 'error');
        return;
    }

    if (!content && !pendingAttachmentFile) return;

    if (pendingAttachmentFile) {
        sendPendingAttachment(content, replyToPayload);
        return;
    }

    pendingMessage = content;
	
	addLocalSendingMessage(content, 'text', {
		reply_to: replyToPayload
	});
 
	if (selectedContactIsGroup) {
        secureEmit('send_group_message', {
            sender_username: username,
            group_name: selectedContact,
            content,
            reply_to: replyToPayload
        });
    } else {
        secureEmit('send_message', {
            sender_username: username,
            receiver_username: selectedContact,
            content,
            reply_to: replyToPayload
        });
    }

    replyingToMessage = null;
    renderReplyPreview();
    messageInput.value = '';
}

function addContact() {
	setPanelStatus(addContactStatus, '', 'info');
    addContactInput.value = '';
    addContactPanel.classList.remove('hidden');
    groupCreationPanel.classList.add('hidden');
}

function submitAddContact() {
    const contactUsername = addContactInput.value.trim();

    if (!contactUsername) {
        setPanelStatus(addContactStatus, 'Please enter a username.', 'error');
        return;
    }

    setPanelStatus(addContactStatus, 'Adding contact...', 'info');

    secureEmit('add_contact', {
        username,
        contact_username: contactUsername
    });
}

function closeAddContact() {
    addContactPanel.classList.add('hidden');
    addContactInput.value = '';
	setPanelStatus(addContactStatus, '', 'info');

}

function openGroupCreator() {
	setPanelStatus(groupCreateStatus, '', 'info');
    addContactPanel.classList.add('hidden');
    const contacts = contactItems.filter((item) => item.type === 'contact');
    if (!contacts.length) {
        alert('You need at least one contact before creating a group chat.');
        return;
    }
    groupMembersList.innerHTML = '';
    contacts.forEach((contact) => {
        const item = document.createElement('label');
        item.className = 'group-member-item';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = contact.name;
        checkbox.name = 'group-member';
        const labelText = document.createElement('span');
        labelText.textContent = contact.display;
        item.appendChild(checkbox);
        item.appendChild(labelText);
        groupMembersList.appendChild(item);
    });
    groupNameInput.value = '';
    groupCreationPanel.classList.remove('hidden');
}

function submitGroupCreation() {
    const groupName = groupNameInput.value.trim();
    if (!groupName) {
		setPanelStatus(groupCreateStatus, 'Please enter a group name.', 'error');
		return;
	}
    const memberUsernames = Array.from(groupMembersList.querySelectorAll('input[type="checkbox"]:checked'))
        .map((checkbox) => checkbox.value);
    if (!memberUsernames.length) {
		setPanelStatus(groupCreateStatus, 'Please select at least one member.', 'error');
		return;
	}
	setPanelStatus(groupCreateStatus, 'Creating group...', 'info');
    secureEmit('create_group_chat', { creator_username: username, group_name: groupName, member_usernames: memberUsernames });
}

function closeGroupCreator() {
    groupCreationPanel.classList.add('hidden');
    groupNameInput.value = '';
    setPanelStatus(groupCreateStatus, '', 'info');

    groupMembersList
        .querySelectorAll('input[type="checkbox"]')
        .forEach((checkbox) => {
            checkbox.checked = false;
        });
}
function createGroupChat() { openGroupCreator(); }

function logout() {
    closeSettingsModal(); 
    secureEmit('set_online_status', { username, status: false });
    secureEmit('logout_user', {
        username,
        device_id: localStorage.getItem(DEVICE_ID_KEY)
    });
    clearSession();
    // Bounce unauthenticated sessions straight out of chat sandbox space cleanly
    window.location.replace('/auth.html');
}

function clearSelectedContact() {
	stopTyping();
	clearTypingDisplay();
    if (!selectedContact) return;
    if (selectedContactIsGroup) {
        secureEmit('leave_group', { username, group_name: selectedContact });
    } else {
        secureEmit('leave_chat', { username });
    }
    selectedContact = null;
    selectedContactIsGroup = false;
	currentGroupIsAdmin = false;
	currentGroupAdmins = [];
    chatTitle.textContent = 'Choose a contact or a group';
    seeMembersButton.classList.add('hidden');
    messages = [];
    hasMoreMessages = false;
    loadingMoreMessages = false;
	
	replyingToMessage = null;
	renderReplyPreview();

	pendingAttachmentFile = null;
	renderAttachmentPreview();
	if (chatLayoutWrapper) chatLayoutWrapper.classList.remove('chat-selected');
	
    renderMessages();
    updateComposerState();
    updateContactList();
    updateLoadMoreButton();
    // cancel any pending conversation requests
    lastRequestedContact = null;
    lastRequestedGroup = null;
    setMainStatus('You have left the chat. Select a contact or group to enter again.', 'info');
	
	
}

function setSelectedContact(name, type) {
    selectedContact = name;
    selectedContactIsGroup = type === 'group';
	
	replyingToMessage = null;
    renderReplyPreview();

    pendingAttachmentFile = null;
    renderAttachmentPreview();

	if (!selectedContactIsGroup) {
		currentGroupIsAdmin = false;
		currentGroupAdmins = [];
	}
	const selectedItem = contactItems.find((item) => {
		return item.name === name && item.type === type;
	});

	if (selectedItem?.removed) {
		chatTitle.textContent = `Group: ${name}`;
		seeMembersButton.classList.add('hidden');
		messages = [];
		currentGroupIsAdmin = false;
		currentGroupAdmins = [];

		messageList.innerHTML = '';

		const removedBox = document.createElement('div');
		removedBox.className = 'message';
		removedBox.textContent = 'You were removed from this group chat and no longer have access to its content.';

		const deleteBtn = document.createElement('button');
		deleteBtn.type = 'button';
		deleteBtn.textContent = 'Delete';
		deleteBtn.className = 'primary-button';
		deleteBtn.style.marginTop = '12px';

		deleteBtn.addEventListener('click', () => {
			openConfirmModal(
				'Delete removed group?',
				'Are you sure you want to delete this removed group from your chat list?',
				() => {
					secureEmit('delete_removed_group', {
						group_name: name
					});
				}
			);
		});

		removedBox.appendChild(document.createElement('br'));
		removedBox.appendChild(deleteBtn);
		messageList.appendChild(removedBox);

		updateComposerState();
		updateContactList();

		if (chatLayoutWrapper) chatLayoutWrapper.classList.add('chat-selected');

		return;
	}
    chatTitle.textContent = selectedContactIsGroup ? `Group: ${selectedContact}` : `Chat with ${selectedContact}`;
    seeMembersButton.classList.toggle('hidden', !selectedContactIsGroup);
    setMainStatus('', 'info');
    if (!selectedContactIsGroup) {
        secureEmit('leave_group', { username: username });
        secureEmit('enter_chat', { username: username, contact_username: selectedContact });
    } else {
        secureEmit('leave_chat', { username: username });
        secureEmit('enter_group', { group_name: selectedContact, username: username });
    }
    messageInput.value = '';
    pendingMessage = null;
    // reset unread count to 0 when opening chat
    clearUnreadCountFor(
		selectedContact,
		selectedContactIsGroup ? 'group' : 'contact'
	);
    hasMoreMessages = false;
    loadingMoreMessages = false;
    updateLoadMoreButton();
	if (chatLayoutWrapper) chatLayoutWrapper.classList.add('chat-selected');
    requestConversation();
    updateContactList();
    updateComposerState();
}

function requestGroupMembers() {
    if (!selectedContact || !selectedContactIsGroup) return;
    secureEmit('get_group_members', { username, group_name: selectedContact });
}

function displayGroupMembers(members) {
    membersList.innerHTML = '';

    if (!members || members.length === 0) {
        const empty = document.createElement('div');
        empty.textContent = 'No members found.';
        empty.className = 'member-item';
        membersList.appendChild(empty);
        return;
    }

    members.forEach((memberName) => {
        const memberEl = document.createElement('div');
        memberEl.className = 'member-item';
        memberEl.style.display = 'flex';
        memberEl.style.justifyContent = 'space-between';
        memberEl.style.alignItems = 'center';
        memberEl.style.gap = '10px';

        const nameSpan = document.createElement('span');
        nameSpan.textContent = memberName;
		if (currentGroupAdmins.includes(memberName)) {
			const adminTag = document.createElement('span');
			adminTag.textContent = 'Admin';
			adminTag.style.marginLeft = '8px';
			adminTag.style.fontSize = '11px';
			adminTag.style.padding = '2px 6px';
			adminTag.style.borderRadius = '999px';
			adminTag.style.background = 'var(--primary)';
			adminTag.style.color = 'white';
			nameSpan.appendChild(adminTag);
		}
        memberEl.appendChild(nameSpan);

        const shouldShowAddButton =
			memberName !== username &&
			!isUserInContacts(memberName) &&
			!pendingAddedContacts.has(memberName);

        if (shouldShowAddButton) {
            const addBtn = document.createElement('button');
            addBtn.type = 'button';
            addBtn.textContent = 'Add contact';
            addBtn.className = 'secondary-button';
            addBtn.style.padding = '6px 10px';
            addBtn.style.fontSize = '12px';
            addBtn.style.marginRight = '0';

            addBtn.addEventListener('click', () => {
				pendingAddedContacts.add(memberName);

				secureEmit('add_contact', {
					username,
					contact_username: memberName
				});

				addBtn.disabled = true;
				addBtn.textContent = 'Adding...';
			});

            memberEl.appendChild(addBtn);
        }
		const shouldShowRemoveButton =
			currentGroupIsAdmin &&
			memberName !== username;

		if (shouldShowRemoveButton) {
			const removeBtn = document.createElement('button');
			removeBtn.type = 'button';
			removeBtn.textContent = 'Remove';
			removeBtn.className = 'contact-options-menu-item danger';
			removeBtn.style.width = 'auto';

			removeBtn.addEventListener('click', () => {
				closeMembersModal();
				openConfirmModal(
					'Remove group member?',
					`Are you sure you want to remove ${memberName} from this group?`,
					() => {
						secureEmit('remove_group_member', {
							group_name: selectedContact,
							member_to_remove: memberName
						});
					}
				);
			});

			memberEl.appendChild(removeBtn);
		}
        membersList.appendChild(memberEl);
    });
}

function openMembersModal() {
    receiptsModal.classList.add('hidden');
    membersModalTitle.textContent = `Members of ${selectedContact}`;
	groupAddMemberButton.classList.toggle('hidden', !currentGroupIsAdmin);
    membersModal.classList.remove('hidden');
    requestGroupMembers();
	
}

function closeMembersModal() { membersModal.classList.add('hidden'); }
function closeReceiptsModal() { receiptsModal.classList.add('hidden'); }

socket.on('typing_status', (data) => {
    if (!data || !data.sender || data.sender === username) return;

    const isRelevant =
        data.chat_type === 'group'
            ? selectedContactIsGroup && selectedContact === data.chat_name
            : !selectedContactIsGroup && selectedContact === data.sender;

    if (!isRelevant) return;

    if (data.is_typing) {
        typingUsers.add(data.sender);
    } else {
        typingUsers.delete(data.sender);
    }

    renderTypingIndicator();
});

socket.on('push_subscription_saved', (data) => {
    if (data?.device_id) {
        localStorage.setItem(DEVICE_ID_KEY, data.device_id);
    }
});
socket.on('connect', () => {
    if (username !== null) {
        setMainStatus('Reconnected to server. Restoring your session...', 'success');
        secureEmit('set_online_status', { username, status: true });
        secureEmit('get_contacts', { username });
        return;
    }

    // Attempt an auto-login check immediately on connection
    const hasSavedSession = checkPersistentToken();
    if (!hasSavedSession) {
        setAuthStatus('Connected to server. Ready to login or register.', 'success');
    }
});

socket.on('connect_error', () => {
    setAuthStatus('Unable to reach the server. Check server availability.', 'error');
});

socket.on('login_successful', (data) => {
    if (appLoadingScreen) appLoadingScreen.classList.add('hidden');
    username = data.username;
    if (data.session_token) {
        saveToken(data.session_token);
    }
    setAuthStatus('Login successful. Loading chat...', 'success');
    startMainScreen();
    checkAndPromptNotificationPermission();

    const userEmail = data.email || '';
    const emailField = document.getElementById('settings-email-input');
    if (emailField) emailField.value = userEmail;

    if (!userEmail) {
        setTimeout(() => {
            setMainStatus('⚠️ Security Warning: You have not set a recovery email! Open Settings to add one.', 'error');
        }, 2000);
    }
});

socket.on('login_failed', (data) => {
    if (appLoadingScreen) appLoadingScreen.classList.add('hidden');
    clearTokenStore(); 
    window.location.replace('/auth.html'); // Kick unverified access requests back to login page bounds
});

socket.on('user_exists_response', (data) => {
    if (!data) { setAuthStatus('Unable to verify username availability.', 'error'); return; }
    if (data.exists) { setAuthStatus('Username already exists. Choose a different username.', 'error'); return; }
    
    const registerUsername = document.getElementById('register-username').value.trim();
    const registerPassword = document.getElementById('register-password').value.trim();
    const registerEmail = document.getElementById('register-email').value.trim(); // ◄--- Read field
    
    socket.emit('create_user', { 
        username: registerUsername, 
        password: registerPassword,
        email: registerEmail
    });
});

socket.on('user_created', (data) => {
    if (!data || !data.success) { setAuthStatus('Account creation failed.', 'error'); return; }
    username = data.username;
    if (data.session_token) {
        saveToken(data.session_token); // Catch token on registration too
    }
    setAuthStatus('Account created successfully. Opening chat...', 'success');
    startMainScreen();
	
	checkAndPromptNotificationPermission();
});

socket.on('contacts_response', (data) => {
    const items = data.items || [];
	contactsLoading = false;
    contactItems = items.map((item) => ({
		name: item.name,
		display: item.name,
		type: item.type,
		removed: item.removed || false,
		is_admin: item.is_admin || false
	}));

    updateContactList();
	if (window.pendingNotificationChat) {
		const requested = window.pendingNotificationChat;

		const exists = contactItems.some((item) => {
			return item.name === requested.name && item.type === requested.type;
		});

		if (exists) {
			setSelectedContact(requested.name, requested.type);
			clearUnreadCountFor(requested.name, requested.type);

			window.pendingNotificationChat = null;
			window.history.replaceState({}, document.title, window.location.pathname);
		}
	}
    contactItems.forEach((item) => {
		if (item.removed) return;
        if (item.type === 'group') {
            secureEmit('get_unread_group_messages_count', {
                username,
                group_name: item.name
            });
        } else {
            secureEmit('get_unread_messages_count', {
                username,
                contact_username: item.name
            });
        }
    });

    secureEmit('get_online_contacts', { username });
});

socket.on('online_contacts_response', (data) => {
    onlineContacts = data.contacts || [];
    updateContactList();
});

socket.on('force_contact_refresh', () => {
    if (username !== null) {
        secureEmit('get_contacts', { username });
        secureEmit('get_online_contacts', { username });
    }
});

socket.on('get_conversation_response', (data) => {
    console.log('get_conversation_response', data);
    if (!data || !data.success) { 
        setMainStatus(data?.message || 'Conversation could not be loaded.', 'error'); 
        if (data?.traceback) {
            console.error('get_conversation_response traceback:', data.traceback);
        }
        loadingMoreMessages = false;
        clearLoadMoreTimer();
        updateLoadMoreButton();
        return; 
    }
    
    if (selectedContactIsGroup || !selectedContact || data.contact_username !== selectedContact) {
        loadingMoreMessages = false;
        clearLoadMoreTimer();
        updateLoadMoreButton();
        return; // Drop stale background response silently
    }
    
    const isOlderPageFetch = loadingMoreMessages || loadingOlderForReplyJump;
	const preserveScroll = isOlderPageFetch;

	if (isOlderPageFetch) {
		messages = (data.messages || []).map(m => ({ ...m, file_url: withAuthToken(m.file_url) })).concat(messages);
	} else {
		messages = (data.messages || []).map(m => ({ ...m, file_url: withAuthToken(m.file_url) }));
	}
    hasMoreMessages = !!data.has_more;
    loadingMoreMessages = false;
    clearLoadMoreTimer();
    renderMessages(preserveScroll);
    updateLoadMoreButton();
	if (pendingReplyJumpMessageId) {
		const found = jumpToMessageById(pendingReplyJumpMessageId);

		if (found) {
			pendingReplyJumpMessageId = null;
			loadingReplyTarget = false;
			loadingOlderForReplyJump = false;
			setMainStatus('', 'info');
		} else if (hasMoreMessages && messages.length) {
			const nextOldestTimestamp = messages[0]?.timestamp;

			if (nextOldestTimestamp) {
				loadingOlderForReplyJump = true;
				requestConversation(nextOldestTimestamp);
			} else {
				pendingReplyJumpMessageId = null;
				loadingReplyTarget = false;
			}
		} else {
			setMainStatus('Original message is not loaded or no longer available.', 'error');
			pendingReplyJumpMessageId = null;
			loadingReplyTarget = false;
			loadingOlderForReplyJump = false;
		}
	}
});

socket.on('get_group_conversation_response', (data) => {
    console.log('get_group_conversation_response', data);
	if (data?.removed) {
		secureEmit('get_contacts', { username });
		return;
	}
    if (!data || !data.success) { 
        setMainStatus(data?.message || 'Group conversation could not be loaded.', 'error'); 
        loadingMoreMessages = false;
        clearLoadMoreTimer();
        updateLoadMoreButton();
        return; 
    }
    
    if (!selectedContactIsGroup || !selectedContact || data.group_name !== selectedContact) {
        loadingMoreMessages = false;
        clearLoadMoreTimer();
        updateLoadMoreButton();
        return; 
    }
    currentGroupIsAdmin = !!data.is_admin;
	currentGroupAdmins = data.admins || [];
    const isOlderPageFetch = loadingMoreMessages || loadingOlderForReplyJump;
	const preserveScroll = isOlderPageFetch;

	if (isOlderPageFetch) {
		messages = (data.messages || []).map(m => ({ ...m, file_url: withAuthToken(m.file_url) })).concat(messages);
	} else {
		messages = (data.messages || []).map(m => ({ ...m, file_url: withAuthToken(m.file_url) }));
	}
    hasMoreMessages = !!data.has_more;
    loadingMoreMessages = false;
    clearLoadMoreTimer();
    renderMessages(preserveScroll);
    updateLoadMoreButton();
	if (pendingReplyJumpMessageId) {
		const found = jumpToMessageById(pendingReplyJumpMessageId);

		if (found) {
			pendingReplyJumpMessageId = null;
			loadingReplyTarget = false;
			loadingOlderForReplyJump = false;
			setMainStatus('', 'info');
		} else if (hasMoreMessages && messages.length) {
			const nextOldestTimestamp = messages[0]?.timestamp;

			if (nextOldestTimestamp) {
				loadingOlderForReplyJump = true;
				requestConversation(nextOldestTimestamp);
			} else {
				pendingReplyJumpMessageId = null;
				loadingReplyTarget = false;
			}
		} else {
			setMainStatus('Original message is not loaded or no longer available.', 'error');
			pendingReplyJumpMessageId = null;
			loadingReplyTarget = false;
			loadingOlderForReplyJump = false;
		}
	}
});

socket.on('send_message_response', (data) => {
    if (!data || !data.success) {
        setMainStatus(data?.message || 'Message failed to send.', 'error');
        return;
    }

    pendingMessage = null;
    requestConversation();
});

socket.on('send_group_message_response', (data) => {
    if (!data || !data.success) {
        setMainStatus(data?.message || 'Group message failed to send.', 'error');
        return;
    }

    pendingMessage = null;
    requestConversation();
});

socket.on('new_message', (data) => {
    if (!selectedContactIsGroup && selectedContact === data.sender_username) {
        messages.push({
			id: data.id,
            sender_username: data.sender_username,
            content: data.content,
            read: data.is_read,
            type: data.type,
            file_url: withAuthToken(data.file_url),
            file_name: data.file_name,
            file_type: data.file_type,
			reply_to: data.reply_to,
            timestamp: data.timestamp
        });
        renderMessages();
    } else {
        const countKey = `${data.sender_username}_contact`;
        unreadCounts[countKey] = (unreadCounts[countKey] || 0) + 1;
        updateContactList();
		syncNativeNotificationBadge();
    }
});

socket.on('new_group_message', (data) => {
    if (selectedContactIsGroup && selectedContact === data.group_name) {
        messages.push({
			id: data.id,
            sender_username: data.sender_username,
            content: data.content,
            read_by: data.read_by,
            type: data.type,
            file_url: withAuthToken(data.file_url),
            file_name: data.file_name,
            file_type: data.file_type,
			reply_to: data.reply_to,
            timestamp: data.timestamp
        });
        renderMessages();
    } else {
        const countKey = `${data.group_name}_group`;
        unreadCounts[countKey] = (unreadCounts[countKey] || 0) + 1;
        updateContactList(); 
		syncNativeNotificationBadge();
    }
});

socket.on('update_read_status', (data) => {
    if (data.type === 'private') {
        if (!selectedContactIsGroup && selectedContact === data.chat_with) {
            lastRequestedContact = selectedContact;
            lastRequestedGroup = null;
            secureEmit('get_conversation', { username: username, contact_username: selectedContact });
        } else {
            secureEmit('get_unread_messages_count', { username: username, contact_username: data.chat_with });
        }
    } else if (data.type === 'group') {
        if (selectedContactIsGroup && selectedContact === data.group_name) {
            lastRequestedGroup = selectedContact;
            lastRequestedContact = null;
            secureEmit('get_group_conversation', { username: username, group_name: selectedContact });
        } else {
            secureEmit('get_unread_group_messages_count', { username: username, group_name: data.group_name });
        }
    }
});

socket.on('add_contact_response', (data) => {
    if (!data) { setMainStatus('Contact request failed.', 'error'); return; }
    if (data.success) {
		addContactPanel.classList.add('hidden');
		addContactInput.value = '';
		setPanelStatus(addContactStatus, '', 'info');

		secureEmit('get_contacts', { username });

		if (!membersModal.classList.contains('hidden')) {
			requestGroupMembers();
		}
	} else {
		setPanelStatus(addContactStatus, data.message || 'User could not be found.', 'error');
	}
});

socket.on('create_group_chat_response', (data) => {
    if (!data) { setMainStatus('Group creation failed.', 'error'); return; }
    if (data.success) {
		setPanelStatus(groupCreateStatus, '', 'info');
		closeGroupCreator();
		secureEmit('get_contacts', { username });
	} else {
		setPanelStatus(groupCreateStatus, data.message || 'Could not create group.', 'error');
	}
});

socket.on('users_in_group_response', (data) => {
    if (!data || !data.success) {
        setMainStatus('Could not load group members.', 'error');
        return;
    }

    currentGroupMembers = data.users || [];
    displayGroupMembers(data.users);
});

socket.on('get_unread_messages_count_response', (data) => {
    if (!data || !data.success) return;

    const countKey = `${data.contact_username}_contact`;

    if (
        recentlyOpenedChats[countKey] &&
        Date.now() - recentlyOpenedChats[countKey] < 3000
    ) {
        return;
    }

    const count = data.count || 0;
    unreadCounts[countKey] = count;
    updateContactList();
	syncNativeNotificationBadge();
});

socket.on('get_unread_group_messages_count_response', (data) => {
    if (!data || !data.success) return;

    const countKey = `${data.group_name}_group`;

    if (
        recentlyOpenedChats[countKey] &&
        Date.now() - recentlyOpenedChats[countKey] < 3000
    ) {
        return;
    }

    const count = data.count || 0;
    unreadCounts[countKey] = count;
    updateContactList();
	syncNativeNotificationBadge();
});

contactList.addEventListener('click', (event) => {
    const item = event.target.closest('.contact-item');
    if (!item || !item.dataset.name) return;
    const targetName = item.dataset.name;
    const targetType = item.dataset.type;
    const isSameContact = selectedContact === targetName && selectedContactIsGroup === (targetType === 'group');
    if (isSameContact) {
        clearSelectedContact();
        return;
    }
    setSelectedContact(targetName, targetType);
});

if (themeToggleButton) {
    themeToggleButton.addEventListener('click', toggleThemeMode);
}
initLoadMoreControl();
if (loginButton) {
	loginButton.addEventListener('click', () => {
		const loginUsername = document.getElementById('login-username').value.trim();
		const loginPassword = document.getElementById('login-password').value.trim();
		if (!loginUsername || !loginPassword) { setAuthStatus('Enter both username and password.', 'error'); return; }
		socket.emit('login', { username: loginUsername, password: loginPassword });
	});
}
if (registerButton){
	registerButton.addEventListener('click', () => {
		const registerUsername = document.getElementById('register-username').value.trim();
		const registerPassword = document.getElementById('register-password').value.trim();
		const registerEmail = document.getElementById('register-email').value.trim(); // ◄--- Read field

		if (!registerUsername || !registerPassword) { 
			setAuthStatus('Choose a username and password.', 'error'); 
			return; 
		}
		
		socket.emit('user_exists', { 
			username: registerUsername,
			password: registerPassword,
			email: registerEmail 
		});
	});
}


if (tabLogin) tabLogin.addEventListener('click', () => switchTab('login'));
if (tabRegister) tabRegister.addEventListener('click', () => switchTab('register'));
addContactButton.addEventListener('click', addContact);
createGroupButton.addEventListener('click', createGroupChat);
groupCreateSubmit.addEventListener('click', submitGroupCreation);
groupCreateCancel.addEventListener('click', closeGroupCreator);
addContactSubmit.addEventListener('click', submitAddContact);
addContactCancel.addEventListener('click', closeAddContact);
if (loadMoreButton) {
    loadMoreButton.addEventListener('click', loadMoreMessages);
}
seeMembersButton.addEventListener('click', openMembersModal);
membersModalClose.addEventListener('click', closeMembersModal);
receiptsModalClose.addEventListener('click', closeReceiptsModal);
pdfClose.addEventListener('click', closePdfModal);
sendButton.addEventListener('click', sendMessage);
logoutButton.addEventListener('click', logout);
if (mobileBackButton) {
    mobileBackButton.addEventListener('click', () => {
        clearSelectedContact();
    });
}
membersModal.addEventListener('click', (event) => {
    if (event.target === membersModal) closeMembersModal();
});
pdfModal.addEventListener('click', (event) => {
    if (event.target === pdfModal) {
        closePdfModal();
    }
});
receiptsModal.addEventListener('click', (event) => {
    if (event.target === receiptsModal) closeReceiptsModal();
});

messageInput.addEventListener('input', () => {
    if (!selectedContact) return;

    if (messageInput.value.trim()) {
        startTyping();
    } else {
        stopTyping();
    }
});

messageInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault();
        stopTyping();
        sendMessage();
    }
});

function leaveCurrentChatSilently() {
    if (!username || !selectedContact) return;

    if (selectedContactIsGroup) {
        secureEmit('leave_group', {
            username,
            group_name: selectedContact
        });
    } else {
        secureEmit('leave_chat', {
            username
        });
    }
}


window.addEventListener('pagehide', () => {
    leaveCurrentChatSilently();

    if (username !== null) {
        secureEmit('set_online_status', { username, status: false });
    }

    socket.disconnect();
});

window.addEventListener('beforeunload', () => {
    leaveCurrentChatSilently();

    if (username !== null) {
        secureEmit('set_online_status', { username, status: false });
    }

    socket.disconnect();
});

function withAuthToken(url) {
    if (!url) return url;
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return url;
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}token=${encodeURIComponent(token)}`;
}

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

function arrayBufferToBase64Url(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
    return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function checkAndPromptNotificationPermission() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;

    try {
        const reg = await navigator.serviceWorker.ready;
        const existingSubscription = await reg.pushManager.getSubscription();

        const response = await fetch('/api/vapid-public-key');
        const currentVapidPublicKey = (await response.text()).trim();

        if (existingSubscription) {
            const existingKey = existingSubscription.options?.applicationServerKey
                ? arrayBufferToBase64Url(existingSubscription.options.applicationServerKey)
                : null;

            if (existingKey === currentVapidPublicKey) {
                // Still valid under the current key — just make sure the server has it
                sendSubscriptionToServer(existingSubscription);
                return;
            }

            // Stale subscription tied to the old (rotated) VAPID key — useless, clear it
            console.log('Push subscription is tied to an old VAPID key, resubscribing...');
            await existingSubscription.unsubscribe();
        }

        if (Notification.permission === 'granted') {
            // Already approved at the browser level — resubscribe silently, no prompt will show
            configurePushSubscription();
            return;
        }

        if (Notification.permission === 'denied') {
            return;
        }

        // Never asked before — show our own prompt before triggering the native one
        openConfirmModal(
            'Enable notifications?',
            'Get notified when you receive new messages, even when Chatter is closed.',
            () => {
                configurePushSubscription();
            }
        );
    } catch (error) {
        console.error('Failed to check notification permission:', error);
    }
}

// Main function to trigger the browser notification prompt and subscribe
async function configurePushSubscription() {
    if (!('serviceWorker' in navigator)) return;

    try {
        const reg = await navigator.serviceWorker.ready;
        
        // 1. Check if we are already subscribed
        const existingSubscription = await reg.pushManager.getSubscription();
        if (existingSubscription) {
            console.log('User already has an active push subscription.');
            sendSubscriptionToServer(existingSubscription);
            return;
        }

        // 2. Fetch your Public VAPID key from your new Flask API endpoint
        const response = await fetch('/api/vapid-public-key');
        const vapidPublicKey = await response.text();
        
        if (!vapidPublicKey) {
            console.error('VAPID Public Key not found on server config.');
            return;
        }

        const convertedKey = urlBase64ToUint8Array(vapidPublicKey);

        // 3. Prompt the user for permission and register with the browser's push server
        const newSubscription = await reg.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: convertedKey
        });

        console.log('Notification permission granted! Subscription created.');
        sendSubscriptionToServer(newSubscription);

    } catch (error) {
        console.error('Could not configure push subscription:', error);
    }
}

function sendSubscriptionToServer(subscription) {
    if (username) {
        secureEmit('save_push_subscription', { 
            username,
            subscription: subscription.toJSON(),
            device_id: localStorage.getItem(DEVICE_ID_KEY)
        });
    }
}
window.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    
    // Explicit security enforcement verification check
    if (localStorage.getItem('chatter_gate_cleared') !== 'true') {
        window.location.replace('/');
        return;
    }
    
    // If no session token is saved in localStorage, skip runtime initialization execution and bounce to auth space
    if (!localStorage.getItem(TOKEN_KEY)) {
        window.location.replace('/auth.html');
        return;
    }

    checkPersistentToken(); 
    
    if ('serviceWorker' in navigator && 'PushManager' in window) {
        navigator.serviceWorker.register('/sw.js')
            .then((registration) => { console.log('Service Worker running logic context:', registration.scope); })
            .catch((error) => { console.error('Service Worker verification error:', error); });
    }
});
settingsButton.addEventListener('click', openSettingsModal);
settingsModalClose.addEventListener('click', closeSettingsModal);

// Close modal if user clicks outside the modal content container box
settingsModal.addEventListener('click', (event) => {
    if (event.target === settingsModal) closeSettingsModal();
});

// Navigate inside Settings: Menu -> Password Change Form
optChangePassword.addEventListener('click', () => {
    settingsMenuOptions.classList.add('hidden');
    passwordChangeForm.classList.remove('hidden');
    settingsStatus.textContent = '';
});

// Navigate inside Settings: Password Change Form -> Menu Back Button
changePasswordBack.addEventListener('click', () => {
    passwordChangeForm.classList.add('hidden');
    settingsMenuOptions.classList.remove('hidden');
    settingsStatus.textContent = '';
    currentPassInput.value = '';
    newPassInput.value = '';
});

// Fire the update request via Socket.IO
changePassSubmit.addEventListener('click', () => {
    const currentPassword = currentPassInput.value.trim();
    const newPassword = newPassInput.value.trim();

    if (!currentPassword || !newPassword) {
        settingsStatus.textContent = 'Please fill out both fields.';
        settingsStatus.className = 'status error';
        return;
    }

    settingsStatus.textContent = 'Updating password...';
    settingsStatus.className = 'status info';

    secureEmit('change_password_in_app', {
        username: username,
        current_password: currentPassword,
        new_password: newPassword
    });
});

// Process the server update execution confirmation
socket.on('change_password_response', (data) => {
    settingsStatus.textContent = data.message;
    if (data.success) {
        settingsStatus.className = 'status success';
        currentPassInput.value = '';
        newPassInput.value = '';
        // Automatically bounce back to settings main menu after a short pause
        setTimeout(() => {
            changePasswordBack.click();
        }, 1500);
    } else {
        settingsStatus.className = 'status error';
    }
});


attachButton.addEventListener('click', () => {
    fileInput.click();
});


function showAttachmentError(message) {
    pendingAttachmentFile = null;
    attachmentPreviewContent.innerHTML = '';

    const errorEl = document.createElement('div');
    errorEl.className = 'status error';
    errorEl.textContent = message;

    attachmentPreviewContent.appendChild(errorEl);
    attachmentPreview.classList.remove('hidden');
}

fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    if (!file || !selectedContact) return;
	
	const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100 MB

    if (file.size > MAX_UPLOAD_SIZE) {
		showAttachmentError(
			`File is too large. Maximum size is ${MAX_UPLOAD_SIZE / 1024 / 1024} MB.`
		);
		fileInput.value = '';
		return;
	}
	
    pendingAttachmentFile = file;
    renderAttachmentPreview();

    fileInput.value = '';
});

socket.on('remove_contact_response', (data) => {
    if (!data || !data.success) {
        setMainStatus(data?.message || 'Could not remove contact.', 'error');
        return;
    }

    if (!selectedContactIsGroup && selectedContact === data.contact_username) {
        clearSelectedContact();
    }

    secureEmit('get_contacts', { username });
});

socket.on('delete_conversation_response', (data) => {
    if (!data || !data.success) {
        setMainStatus(data?.message || 'Could not delete conversation.', 'error');
        return;
    }

    if (
        selectedContact === data.target_name &&
        selectedContactIsGroup === (data.target_type === 'group')
    ) {
        messages = [];
        renderMessages();
    }

    secureEmit('get_contacts', { username });
});

groupAddMemberButton.addEventListener('click', () => {
    groupAddMemberInput.value = '';
    setPanelStatus(groupMemberStatus, '', 'info');
    renderGroupAddContactList();
    groupAddMemberPanel.classList.remove('hidden');
});

groupAddMemberCancel.addEventListener('click', () => {
    groupAddMemberPanel.classList.add('hidden');
    groupAddMemberInput.value = '';
    setPanelStatus(groupMemberStatus, '', 'info');
});

groupAddMemberSubmit.addEventListener('click', () => {
    const checkedContacts = Array.from(
        groupAddContactList.querySelectorAll('input[type="checkbox"]:checked')
    ).map((checkbox) => checkbox.value);

    const typedMember = groupAddMemberInput.value.trim();

    const membersToAdd = [...checkedContacts];

    if (typedMember && !membersToAdd.includes(typedMember)) {
        membersToAdd.push(typedMember);
    }

    if (!membersToAdd.length) {
        setPanelStatus(groupMemberStatus, 'Please select or enter a user.', 'error');
        return;
    }

    setPanelStatus(groupMemberStatus, 'Adding member...', 'info');

    membersToAdd.forEach((memberName) => {
        secureEmit('add_group_member', {
            group_name: selectedContact,
            new_member: memberName
        });
    });
});

socket.on('group_member_update_response', (data) => {
    if (!data || !data.success) {
        setPanelStatus(groupMemberStatus, data?.message || 'Could not update group members.', 'error');
        return;
    }

    setPanelStatus(groupMemberStatus, '', 'info');
    groupAddMemberPanel.classList.add('hidden');
    groupAddMemberInput.value = '';

    requestGroupMembers();
    requestConversation();
    secureEmit('get_contacts', { username });
});

socket.on('force_group_refresh', (data) => {
    if (
        selectedContactIsGroup &&
        selectedContact === data.group_name
    ) {
        requestGroupMembers();
        requestConversation();
    }
});


socket.on('delete_removed_group_response', (data) => {
    if (!data || !data.success) {
        setMainStatus(data?.message || 'Could not delete removed group.', 'error');
        return;
    }

    if (selectedContactIsGroup && selectedContact === data.group_name) {
        clearSelectedContact();
    }

    secureEmit('get_contacts', { username });
});

socket.on('force_group_deleted', (data) => {
    if (
        selectedContactIsGroup &&
        selectedContact === data.group_name
    ) {
        clearSelectedContact();
    }

    secureEmit('get_contacts', { username });
});
socket.on('delete_group_chat_response', (data) => {
    if (!data || !data.success) {
        setMainStatus(data?.message || 'Could not delete group chat.', 'error');
        return;
    }

    if (selectedContactIsGroup && selectedContact === data.group_name) {
        clearSelectedContact();
    }

    secureEmit('get_contacts', { username });
});

socket.on('force_conversation_refresh', (data) => {
    if (!selectedContact) return;

    if (
        data.type === 'group' &&
        selectedContactIsGroup &&
        selectedContact === data.chat_name
    ) {
        requestConversation();
    }

    if (
        data.type === 'contact' &&
        !selectedContactIsGroup &&
        selectedContact === data.chat_name
    ) {
        requestConversation();
    }
});



socket.on('message_action_response', (data) => {
    if (!data || !data.success) {
        setMainStatus(data?.message || 'Message action failed.', 'error');
        return;
    }

    requestConversation();
});



// ==================== Recovery Email Save Logic Bindings ====================
const settingsEmailInput = document.getElementById('settings-email-input');
const settingsEmailSubmit = document.getElementById('settings-email-submit');

if (settingsEmailSubmit) {
    settingsEmailSubmit.addEventListener('click', () => {
        const targetEmail = settingsEmailInput.value.trim();
        if (!targetEmail) {
            setPanelStatus(document.getElementById('settings-status'), 'Please provide a valid email format.', 'error');
            return;
        }

        setPanelStatus(document.getElementById('settings-status'), 'Saving email metadata...', 'info');
        secureEmit('save_recovery_email', { email: targetEmail });
    });
}

socket.on('save_recovery_email_response', (data) => {
    const statusBox = document.getElementById('settings-status');
    if (data.success) {
        setPanelStatus(statusBox, data.message, 'success');
        setMainStatus('Recovery email updated successfully.', 'success');
    } else {
        setPanelStatus(statusBox, data.message || 'Failed to update email record.', 'error');
    }
});




