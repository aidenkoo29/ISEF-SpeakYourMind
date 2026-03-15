document.addEventListener('DOMContentLoaded', () => {
    const authScreen = document.getElementById('auth-screen');
    const appShell = document.querySelector('.app-shell');
    const authTabLogin = document.getElementById('auth-tab-login');
    const authTabSignup = document.getElementById('auth-tab-signup');
    const authError = document.getElementById('auth-error');
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const loginUsernameInput = document.getElementById('login-username');
    const loginPasswordInput = document.getElementById('login-password');
    const signupUsernameInput = document.getElementById('signup-username');
    const signupPasswordInput = document.getElementById('signup-password');
    const logoutBtn = document.getElementById('logout-btn');
    const cardContainer = document.getElementById('card-container');
    const selectedCardsContainer = document.getElementById('selected-cards');
    const suggestedCardsContainer = document.getElementById('suggested-cards');
    const tabsContainer = document.querySelector('.tabs');
    const resetBtn = document.getElementById('reset-btn');
    const augmentationBtn = document.getElementById('add-card-btn');
    const recordBtn = document.getElementById('record-btn');
    const augmentedPopup = document.getElementById('augmented-popup');
    const closeBtn = document.querySelector('.close-btn');
    const augmentedCardsPopupContainer = document.getElementById('augmented-cards-popup-container');
    const suggestionPopup = document.getElementById('suggestion-popup');
    const suggestionCloseBtn = document.getElementById('suggestion-close-btn');
    const refreshSuggestionsBtn = document.getElementById('refresh-suggestions-btn');
    const suggestedNewCardsContainer = document.getElementById('suggested-new-cards-container');
    const toastContainer = document.getElementById('toast-container');
    const appSidebar = document.getElementById('app-sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarAacBtn = document.getElementById('sidebar-aac-btn');
    const sidebarCommunityBtn = document.getElementById('sidebar-community-btn');
    const sidebarSettingsBtn = document.getElementById('sidebar-settings-btn');
    const aacView = document.getElementById('aac-view');
    const communityView = document.getElementById('community-view');
    const settingsView = document.getElementById('settings-view');
    const communitySearchInput = document.getElementById('community-search-input');
    const communitySearchBtn = document.getElementById('community-search-btn');
    const communityResults = document.getElementById('community-results');
    const communityDetailPopup = document.getElementById('community-detail-popup');
    const communityDetailCloseBtn = document.getElementById('community-detail-close-btn');
    const communityDetailTitle = document.getElementById('community-detail-title');
    const communityDetailBody = document.getElementById('community-detail-body');
    const communityDetailAudioBtn = document.getElementById('community-detail-audio-btn');
    const communityDetailCopyBtn = document.getElementById('community-detail-copy-btn');
    const communitySharePopup = document.getElementById('community-share-popup');
    const communityShareCloseBtn = document.getElementById('community-share-close-btn');
    const openShareBtn = document.getElementById('open-share-btn');
    const shareCardSearch = document.getElementById('share-card-search');
    const shareCardResults = document.getElementById('share-card-results');
    const shareCardSelected = document.getElementById('share-card-selected');
    const shareTimeInput = document.getElementById('share-time');
    const sharePlaceInput = document.getElementById('share-place');
    const shareOccasionInput = document.getElementById('share-occasion');
    const shareTagsInput = document.getElementById('share-tags');
    const shareSubmitBtn = document.getElementById('share-submit-btn');
    const settingsUsername = document.getElementById('settings-username');
    const settingsPasswordForm = document.getElementById('settings-password-form');
    const currentPasswordInput = document.getElementById('current-password');
    const newPasswordInput = document.getElementById('new-password');
    const settingsMessage = document.getElementById('settings-message');
    let shareSelectedCard = null;

    let aacData = [];
    let selectedCards = [];
    let favoriteKeys = new Set();
    const audioCache = new Map();
    let selectionUpdateTimer = null;
    const MAX_AUDIO_PREFETCH = 30;
    const popups = [augmentedPopup, suggestionPopup, communityDetailPopup, communitySharePopup];
    popups.forEach(popup => enablePopupDragging(popup));
    let appInitialized = false;

    function initApp() {
        if (appInitialized) return;
        appInitialized = true;
        fetch('../data/aac_library.csv')
            .then(response => response.text())
            .then(data => {
                const rows = data.trim().split('\n').slice(1);
                aacData = rows.map(row => {
                    const [category, word] = row.split(',');
                    return { category, word, image: `../aac_images/${category}/${word}.png` };
                });
                favoriteKeys = loadFavorites();
                renderTabs();
                renderCards('All');
            });
    }

    function renderTabs() {
    const categories = ['All', 'Favorites', ...new Set(aacData.map(item => item.category))];
    tabsContainer.innerHTML = '';
    categories.forEach(category => {
        const tabBtn = document.createElement('button');
        tabBtn.className = 'tab-btn';
        tabBtn.textContent = category === 'All' ? 'All' : category;
        tabBtn.dataset.category = category;

        if (category === 'All') tabBtn.classList.add('active');

        tabBtn.addEventListener('click', () => {
            document.querySelector('.tab-btn.active').classList.remove('active');
            tabBtn.classList.add('active');
            renderCards(category);
        });

        tabsContainer.appendChild(tabBtn);
    });
}


    function renderCards(category) {
        cardContainer.innerHTML = '';
        let filteredData = [];
        if (category === 'All') {
            filteredData = aacData;
        } else if (category === 'Favorites') {
            filteredData = aacData.filter(item => favoriteKeys.has(makeFavoriteKey(item)));
        } else {
            filteredData = aacData.filter(item => item.category === category);
        }
        if (filteredData.length === 0) {
            cardContainer.innerHTML = '<p>No cards to show.</p>';
            return;
        }
        filteredData.forEach(item => {
            const card = createCard(item);
            card.addEventListener('click', () => addToSelected(item));
            cardContainer.appendChild(card);
        });
        prefetchAudio(filteredData);
    }

    function createCard(item) {
        const card = document.createElement('div');
        card.className = 'card';
        const isFavorite = favoriteKeys.has(makeFavoriteKey(item));
        card.innerHTML = `
            <button type="button" class="favorite-toggle ${isFavorite ? 'active' : ''}" aria-label="Favorite"></button>
            <img src="${normalizeAssetPath(item.image)}" alt="${item.word}">
            <p>${item.word}</p>
        `;
        const favBtn = card.querySelector('.favorite-toggle');
        favBtn.addEventListener('click', (event) => {
            event.stopPropagation();
            toggleFavorite(item, favBtn);
        });
        return card;
    }

    function addToSelected(item) {
        selectedCards.push(item);
        renderSelectedCards();
        playAudio(item);
    }

    function playAudio(item) {
        const audio = getCachedAudio(item);
        if (!audio) return;
        audio.currentTime = 0;
        audio.play().catch(() => {
            // Ignore autoplay/interaction errors; card clicks are user-driven anyway.
        });
    }

    function playAudioUrl(url) {
        if (!url) {
            showToast('Audio path not available.', 'error');
            return;
        }
        const key = `url:::${url}`;
        let audio = audioCache.get(key);
        if (!audio) {
            audio = new Audio(normalizeAssetPath(url));
            audio.preload = 'auto';
            audioCache.set(key, audio);
        }
        audio.currentTime = 0;
        audio.play().catch(() => {
            // Ignore autoplay/interaction errors; this is user-initiated.
        });
    }

    function normalizeAssetPath(path) {
        if (!path) return path;
        if (
            path.startsWith('http://') ||
            path.startsWith('https://') ||
            path.startsWith('data:') ||
            path.startsWith('blob:') ||
            path.startsWith('../') ||
            path.startsWith('/')
        ) {
            return path;
        }
        if (path.startsWith('aac_images/') || path.startsWith('aac_audios/')) {
            return `../${path}`;
        }
        return path;
    }

    function stripFrontendPrefix(path) {
        if (!path) return path;
        return path.startsWith('../') ? path.slice(3) : path;
    }

    let authToken = null;

    function getAuthToken() {
        return authToken;
    }

    function setAuthError(message = '') {
        if (!authError) return;
        if (!message) {
            authError.style.display = 'none';
            authError.textContent = '';
            return;
        }
        authError.textContent = message;
        authError.style.display = 'block';
    }

    function setAuthMode(mode) {
        const isLogin = mode === 'login';
        authTabLogin.classList.toggle('active', isLogin);
        authTabSignup.classList.toggle('active', !isLogin);
        loginForm.style.display = isLogin ? 'flex' : 'none';
        signupForm.style.display = isLogin ? 'none' : 'flex';
        setAuthError('');
    }

    function showAuthScreen() {
        document.body.classList.remove('is-authenticated');
        authScreen.style.display = 'flex';
        appShell.classList.remove('is-visible');
    }

    function showAppScreen() {
        document.body.classList.add('is-authenticated');
        authScreen.style.display = 'none';
        appShell.classList.add('is-visible');
        appSidebar.classList.remove('collapsed');
        initApp();
        setActiveView('aac');
        refreshSettings();
    }

    function formatAuthError(code) {
        switch (code) {
            case 'invalid_credentials':
                return 'Invalid username or password.';
            case 'unauthorized':
                return 'Please log in again.';
            case 'user_exists':
                return 'That username is already taken.';
            case 'username_too_short':
                return 'Username must be at least 3 characters.';
            case 'username_too_long':
                return 'Username must be 40 characters or fewer.';
            case 'password_too_short':
                return 'Password must be at least 8 characters.';
            case 'password_too_long':
                return 'Password must be 128 characters or fewer.';
            default:
                return 'Something went wrong. Please try again.';
        }
    }

    function setSettingsMessage(message, type = 'success') {
        if (!settingsMessage) return;
        settingsMessage.textContent = message;
        settingsMessage.classList.remove('success', 'error');
        settingsMessage.classList.add(type);
        settingsMessage.style.display = 'block';
    }

    async function refreshSettings() {
        if (!settingsUsername) return;
        const token = getAuthToken();
        if (!token) {
            settingsUsername.textContent = '-';
            return;
        }
        try {
            const response = await fetch('http://127.0.0.1:8000/auth/me', {
                headers: { Authorization: `Bearer ${token}` }
            });
            const result = await response.json();
            settingsUsername.textContent = result.user?.username || '-';
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }

    function clearAuth() {
        authToken = null;
        loginUsernameInput.value = '';
        loginPasswordInput.value = '';
        signupUsernameInput.value = '';
        signupPasswordInput.value = '';
        currentPasswordInput.value = '';
        newPasswordInput.value = '';
        settingsMessage.style.display = 'none';
        setAuthError('');
        showAuthScreen();
    }

    authTabLogin.addEventListener('click', () => setAuthMode('login'));
    authTabSignup.addEventListener('click', () => setAuthMode('signup'));

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        setAuthError('');
        const username = loginUsernameInput.value.trim();
        const password = loginPasswordInput.value;
        if (!username || !password) {
            setAuthError('Enter both username and password.');
            return;
        }
        try {
            const response = await fetch('http://127.0.0.1:8000/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const result = await response.json();
            if (result.error || !result.token) {
                setAuthError(formatAuthError(result.error));
                return;
            }
            authToken = result.token;
            showAppScreen();
        } catch (error) {
            console.error('Login failed:', error);
            setAuthError('Login failed. Please try again.');
        }
    });

    signupForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        setAuthError('');
        const username = signupUsernameInput.value.trim();
        const password = signupPasswordInput.value;
        if (!username || !password) {
            setAuthError('Enter both username and password.');
            return;
        }
        try {
            const response = await fetch('http://127.0.0.1:8000/auth/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const result = await response.json();
            if (result.error || !result.token) {
                setAuthError(formatAuthError(result.error));
                return;
            }
            authToken = result.token;
            showAppScreen();
        } catch (error) {
            console.error('Signup failed:', error);
            setAuthError('Signup failed. Please try again.');
        }
    });

    function resetPopupPosition(popupEl) {
        if (!popupEl) return;
        const content = popupEl.querySelector('.popup-content');
        if (!content) return;
        content.style.left = '';
        content.style.top = '';
        content.style.margin = '';
        content.style.position = '';
    }

    function enablePopupDragging(popupEl) {
        if (!popupEl) return;
        const content = popupEl.querySelector('.popup-content');
        if (!content) return;

        let isDragging = false;
        let startX = 0;
        let startY = 0;
        let startLeft = 0;
        let startTop = 0;

        function onMouseMove(event) {
            if (!isDragging) return;
            const dx = event.clientX - startX;
            const dy = event.clientY - startY;
            const nextLeft = startLeft + dx;
            const nextTop = startTop + dy;
            const maxLeft = window.innerWidth - content.offsetWidth - 8;
            const maxTop = window.innerHeight - content.offsetHeight - 8;
            content.style.left = `${Math.min(Math.max(8, nextLeft), Math.max(8, maxLeft))}px`;
            content.style.top = `${Math.min(Math.max(8, nextTop), Math.max(8, maxTop))}px`;
        }

        function onMouseUp() {
            if (!isDragging) return;
            isDragging = false;
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        }

        content.addEventListener('mousedown', (event) => {
            if (event.button !== 0) return;
            if (event.target.closest('button, input, textarea, select, a, label, .close-btn')) return;
            const handle = event.target.closest('.popup-header, h3, .popup-content');
            if (!handle) return;

            const rect = content.getBoundingClientRect();
            content.style.position = 'absolute';
            content.style.margin = '0';
            content.style.left = `${rect.left}px`;
            content.style.top = `${rect.top}px`;

            isDragging = true;
            startX = event.clientX;
            startY = event.clientY;
            startLeft = rect.left;
            startTop = rect.top;

            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });
    }

    function removeFromSelected(index) {
        selectedCards.splice(index, 1);
        renderSelectedCards();
    }

    function renderSelectedCards() {
        selectedCardsContainer.innerHTML = '';
        selectedCards.forEach((item, index) => {
            const card = createCard(item);
            card.addEventListener('click', () => removeFromSelected(index));
            selectedCardsContainer.appendChild(card);
        });
        scheduleSelectionUpdate();
    }

    function makeFavoriteKey(item) {
        return `${item.category}|||${item.word}`;
    }

    function loadFavorites() {
        try {
            const raw = localStorage.getItem('aac_favorites');
            if (!raw) return new Set();
            const parsed = JSON.parse(raw);
            return new Set(Array.isArray(parsed) ? parsed : []);
        } catch {
            return new Set();
        }
    }

    function saveFavorites() {
        localStorage.setItem('aac_favorites', JSON.stringify(Array.from(favoriteKeys)));
    }

    function toggleFavorite(item, buttonEl) {
        const key = makeFavoriteKey(item);
        if (favoriteKeys.has(key)) {
            favoriteKeys.delete(key);
            buttonEl.classList.remove('active');
        } else {
            favoriteKeys.add(key);
            buttonEl.classList.add('active');
        }
        saveFavorites();
        const activeCategory = document.querySelector('.tab-btn.active')?.dataset.category || 'All';
        if (activeCategory === 'Favorites') {
            renderCards('Favorites');
        }
    }

    const suggestionBtn = document.getElementById('suggestion-btn');

    suggestionBtn.addEventListener('click', async () => {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        suggestionBtn.appendChild(spinner);
        suggestionBtn.disabled = true;

        try {
            const response = await fetch('http://127.0.0.1:8000/suggest-cards');
            const suggestions = await response.json();
            renderSuggestedCards(suggestions);
        } catch (error) {
            console.error('Error fetching suggestions:', error);
        } finally {
            suggestionBtn.removeChild(spinner);
            suggestionBtn.disabled = false;
        }
    });

    augmentationBtn.addEventListener('click', async (event) => {
        event.preventDefault();
        resetPopupPosition(suggestionPopup);
        suggestionPopup.style.display = 'flex';
        await loadNewCardSuggestions();
    });

    refreshSuggestionsBtn.addEventListener('click', async () => {
        await loadNewCardSuggestions();
    });

    function showAugmentedPopup(newCards) {
        augmentedCardsPopupContainer.innerHTML = '';
        newCards.forEach(item => {
            const card = createCard(item);
            augmentedCardsPopupContainer.appendChild(card);
        });
        resetPopupPosition(augmentedPopup);
        augmentedPopup.style.display = 'flex';
    }

    closeBtn.addEventListener('click', () => {
        augmentedPopup.style.display = 'none';
    });

    suggestionCloseBtn.addEventListener('click', () => {
        suggestionPopup.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target === augmentedPopup) {
            augmentedPopup.style.display = 'none';
        }
        if (event.target === suggestionPopup) {
            suggestionPopup.style.display = 'none';
        }
        if (event.target === communityDetailPopup) {
            communityDetailPopup.style.display = 'none';
        }
        if (event.target === communitySharePopup) {
            communitySharePopup.style.display = 'none';
        }
    });

    function renderSuggestedCards(suggestions = []) {
        suggestedCardsContainer.innerHTML = '';
        suggestions.forEach(item => {
            const card = createCard(item);
            card.addEventListener('click', () => {
                addToSelected(item);
            });
            suggestedCardsContainer.appendChild(card);
        });
        prefetchAudio(suggestions);
    }

    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    function renderCommunityResults(cards = []) {
        communityResults.innerHTML = '';

        if (!cards || cards.length === 0) {
            communityResults.innerHTML = '<p>No results found.</p>';
            return;
        }

        cards.forEach(card => {
            const wrapper = document.createElement('div');
            wrapper.className = 'community-card';

            const isInLibrary = aacData.some(item => item.category === card.category && item.word === card.name);

            wrapper.innerHTML = `
                <div class="community-card-image">
                    ${card.image ? `<img src="${normalizeAssetPath(card.image)}" alt="${card.name || ''}">` : ''}
                </div>
                <div class="community-card-body">
                    <strong>${card.name}</strong>
                    <span>${card.category || ''}</span>
                    <span class="community-card-creator">${card.creator_id ? `By ${card.creator_id}` : 'By Unknown'}</span>
                </div>
                <div class="community-card-actions">
                    <button type="button" class="community-card-cta" data-card-id="${card.id}">
                        ${isInLibrary ? 'Added' : 'Add'}
                    </button>
                </div>
            `;

            wrapper.addEventListener('click', (event) => {
                const target = event.target;
                if (target.closest('.community-card-cta')) {
                    return;
                }
                openCommunityDetail(card.id);
            });

            const ctaBtn = wrapper.querySelector('button[data-card-id]');
            if (isInLibrary) {
                ctaBtn.disabled = true;
            }
            ctaBtn.addEventListener('click', async (event) => {
                event.stopPropagation();
                if (ctaBtn.disabled) return;
                ctaBtn.textContent = 'Adding...';
                ctaBtn.disabled = true;
                await copyCommunityCard(card.id);
                ctaBtn.textContent = 'Added';
            });

            communityResults.appendChild(wrapper);
        });
    }

    async function loadCommunityResults(query = '') {
        communityResults.innerHTML = '<div class="spinner"></div>';
        try {
            const response = await fetch(`http://127.0.0.1:8000/community/search?q=${encodeURIComponent(query)}`);
            const result = await response.json();
            renderCommunityResults(result.results || []);
        } catch (error) {
            console.error('Error loading community results:', error);
            communityResults.innerHTML = '';
            showToast('Failed to search the community.', 'error');
        }
    }

    async function openCommunityDetail(cardId) {
        if (!cardId) return;
        try {
            const response = await fetch(`http://127.0.0.1:8000/community/card/${cardId}`);
            const result = await response.json();
            if (result.error || !result.card) {
                showToast('Card not found.', 'error');
                return;
            }

            const card = result.card;
            communityDetailTitle.textContent = card.name || '';

            const tags = (card.tags || []).join(', ');
            const contextLines = [
                card.context_time ? `Time: ${card.context_time}` : '',
                card.context_place ? `Place: ${card.context_place}` : '',
                card.context_occasion ? `Occasion: ${card.context_occasion}` : '',
            ].filter(Boolean);

            communityDetailBody.innerHTML = `
                ${card.image ? `<img src="${normalizeAssetPath(card.image)}" alt="${card.name || ''}">` : ''}
                <p>Category: ${card.category || ''}</p>
                ${tags ? `<p>Tags: ${tags}</p>` : ''}
                ${contextLines.map(line => `<p>${line}</p>`).join('')}
            `;

            communityDetailAudioBtn.onclick = () => playAudioUrl(card.audio);
            communityDetailCopyBtn.onclick = () => copyCommunityCard(card.id);
            resetPopupPosition(communityDetailPopup);
            communityDetailPopup.style.display = 'flex';
        } catch (error) {
            console.error('Error opening community detail:', error);
            showToast('Failed to load card details.', 'error');
        }
    }

    async function copyCommunityCard(cardId) {
        try {
            const response = await fetch('http://127.0.0.1:8000/community/copy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: cardId })
            });
            const result = await response.json();
            if (result.error || !result.copied) {
                showToast('Failed to copy the card.', 'error');
                return;
            }

            const copied = result.copied;
            if (!aacData.some(card => card.category === copied.category && card.word === copied.word)) {
                aacData.push({
                    category: copied.category,
                    word: copied.word,
                    image: normalizeAssetPath(copied.image) || `../aac_images/${copied.category}/${copied.word}.png`
                });
                renderTabs();
                const activeCategory = document.querySelector('.tab-btn.active')?.dataset.category || 'All';
                renderCards(activeCategory);
            }
            showToast('Added to your library.', 'success');
        } catch (error) {
            console.error('Error copying community card:', error);
            showToast('Failed to copy the card.', 'error');
        }
    }

    function renderSharePicker(query = '') {
        shareCardResults.innerHTML = '';
        const q = query.trim().toLowerCase();
        const sorted = [...aacData].sort((a, b) => a.word.localeCompare(b.word, 'en'));
        const filtered = q
            ? sorted.filter(item =>
                item.word.toLowerCase().includes(q) ||
                item.category.toLowerCase().includes(q)
            )
            : sorted.slice(0, 24);

        if (filtered.length === 0) {
            shareCardResults.innerHTML = '<p>No matching cards.</p>';
            return;
        }

        filtered.forEach(item => {
            const card = document.createElement('div');
            card.className = 'share-card-item';
            card.innerHTML = `
                <img src="${normalizeAssetPath(item.image)}" alt="${item.word}">
                <strong>${item.word}</strong>
                <span>${item.category}</span>
            `;
            card.addEventListener('click', () => {
                shareSelectedCard = item;
                shareCardSelected.style.display = 'flex';
                shareCardSelected.innerHTML = `
                    <img src="${normalizeAssetPath(item.image)}" alt="${item.word}">
                    <div>
                        <strong>${item.word}</strong>
                        <span>${item.category}</span>
                    </div>
                `;
            });
            shareCardResults.appendChild(card);
        });
    }

    function openSharePopup() {
        shareSelectedCard = null;
        shareCardSearch.value = '';
        shareCardSelected.style.display = 'none';
        shareCardSelected.innerHTML = '';
        renderSharePicker('');
        shareTimeInput.value = '';
        sharePlaceInput.value = '';
        shareOccasionInput.value = '';
        shareTagsInput.value = '';
        resetPopupPosition(communitySharePopup);
        communitySharePopup.style.display = 'flex';
    }

    async function submitShare() {
        if (!shareSelectedCard) {
            showToast('Selected card not found.', 'error');
            return;
        }
        const card = shareSelectedCard;

        const tags = shareTagsInput.value
            .split(',')
            .map(tag => tag.trim())
            .filter(Boolean);

        const payload = {
            name: card.word,
            category: card.category,
            tags,
            context_time: shareTimeInput.value.trim(),
            context_place: sharePlaceInput.value.trim(),
            context_occasion: shareOccasionInput.value.trim(),
            image: stripFrontendPrefix(card.image || `../aac_images/${card.category}/${card.word}.png`),
            audio: stripFrontendPrefix(`../aac_audios/${card.category}/${card.word}.mp3`)
        };

        try {
            const authToken = getAuthToken();
            const headers = { 'Content-Type': 'application/json' };
            if (authToken) {
                headers.Authorization = `Bearer ${authToken}`;
            }
            const response = await fetch('http://127.0.0.1:8000/community/share', {
                method: 'POST',
                headers,
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (!result.card) {
                showToast('Failed to share the card.', 'error');
                return;
            }
            communitySharePopup.style.display = 'none';
            await loadCommunityResults(communitySearchInput.value.trim());
            showToast('Shared to the community.', 'success');
        } catch (error) {
            console.error('Error sharing community card:', error);
            showToast('Failed to share the card.', 'error');
        }
    }

    function setActiveView(viewName) {
        const showSettings = viewName === 'settings';
        const showCommunity = viewName === 'community';
        const showAac = !showCommunity && !showSettings;
        aacView.classList.toggle('active', showAac);
        communityView.classList.toggle('active', showCommunity);
        settingsView.classList.toggle('active', showSettings);
        sidebarAacBtn.classList.toggle('active', showAac);
        sidebarCommunityBtn.classList.toggle('active', showCommunity);
        sidebarSettingsBtn.classList.toggle('active', showSettings);
        document.body.classList.toggle('view-community', showCommunity);
        document.body.classList.toggle('view-settings', showSettings);
        if (showCommunity) {
            loadCommunityResults(communitySearchInput.value.trim());
        }
    }

    sidebarToggle.addEventListener('click', () => {
        appSidebar.classList.toggle('collapsed');
    });

    sidebarAacBtn.addEventListener('click', () => {
        setActiveView('aac');
    });

    sidebarCommunityBtn.addEventListener('click', () => {
        setActiveView('community');
    });

    sidebarSettingsBtn.addEventListener('click', () => {
        setActiveView('settings');
        refreshSettings();
    });
    logoutBtn.addEventListener('click', () => {
        sidebarAacBtn.classList.remove('active');
        sidebarCommunityBtn.classList.remove('active');
        sidebarSettingsBtn.classList.remove('active');
        logoutBtn.classList.add('active');
        setTimeout(() => {
            const confirmed = window.confirm('Are you sure you want to log out?');
            if (!confirmed) {
                logoutBtn.classList.remove('active');
                return;
            }
            clearAuth();
        }, 0);
    });

    settingsPasswordForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const token = getAuthToken();
        if (!token) {
            setSettingsMessage('Please log in again.', 'error');
            return;
        }
        const currentPassword = currentPasswordInput.value;
        const newPassword = newPasswordInput.value;
        if (!currentPassword || !newPassword) {
            setSettingsMessage('Enter current and new password.', 'error');
            return;
        }
        try {
            const response = await fetch('http://127.0.0.1:8000/auth/change-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
            });
            const result = await response.json();
            if (result.error) {
                setSettingsMessage(formatAuthError(result.error), 'error');
                return;
            }
            currentPasswordInput.value = '';
            newPasswordInput.value = '';
            setSettingsMessage('Password updated.', 'success');
        } catch (error) {
            console.error('Password update failed:', error);
            setSettingsMessage('Password update failed.', 'error');
        }
    });

    communityDetailCloseBtn.addEventListener('click', () => {
        communityDetailPopup.style.display = 'none';
    });

    communityShareCloseBtn.addEventListener('click', () => {
        communitySharePopup.style.display = 'none';
    });

    communitySearchBtn.addEventListener('click', async () => {
        await loadCommunityResults(communitySearchInput.value.trim());
    });

    communitySearchInput.addEventListener('keydown', async (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            await loadCommunityResults(communitySearchInput.value.trim());
        }
    });

    openShareBtn.addEventListener('click', () => {
        openSharePopup();
    });

    shareCardSearch.addEventListener('input', (event) => {
        renderSharePicker(event.target.value);
    });

    shareSubmitBtn.addEventListener('click', async () => {
        await submitShare();
    });

    async function loadNewCardSuggestions() {
        suggestedNewCardsContainer.innerHTML = '<div class="spinner"></div>';
        try {
            const response = await fetch('http://127.0.0.1:8000/suggest-new-cards', { method: 'POST' });
            const result = await response.json();
            renderNewCardSuggestions(result.suggestions || []);
        } catch (error) {
            console.error('Error loading new card suggestions:', error);
            suggestedNewCardsContainer.innerHTML = '';
            showToast('Failed to load suggested cards.', 'error');
        }
    }

    function renderNewCardSuggestions(suggestions) {
        if (suggestions.length === 0) {
            suggestedNewCardsContainer.innerHTML = '<p>No new cards to suggest.</p>';
            return;
        }

        const list = document.createElement('div');
        list.className = 'suggestion-list';

        suggestions.forEach(item => {
            const exists = aacData.some(card => card.category === item.category && card.word === item.word);

            const row = document.createElement('div');
            row.className = 'suggestion-item';

            const meta = document.createElement('div');
            meta.className = 'suggestion-meta';
            meta.innerHTML = `<strong>${item.word}</strong><span>${item.category}</span>`;

            const actions = document.createElement('div');
            actions.className = 'suggestion-actions';

            const button = document.createElement('button');
            button.textContent = exists ? 'Already Added' : 'Generate';
            button.disabled = exists;

            const status = document.createElement('span');

            button.addEventListener('click', async () => {
                button.disabled = true;
                button.textContent = 'Generating...';
                status.textContent = '';

                try {
                    const response = await fetch('http://127.0.0.1:8000/generate-card', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ category: item.category, word: item.word })
                    });
                    const result = await response.json();
                    pollJobStatus(result.job_id, item, button, status);
                } catch (error) {
                    console.error('Error generating card:', error);
                    button.disabled = false;
                    button.textContent = 'Generate';
                    showToast('Failed to generate the card.', 'error');
                }
            });

            actions.appendChild(button);
            actions.appendChild(status);
            row.appendChild(meta);
            row.appendChild(actions);
            list.appendChild(row);
        });

        suggestedNewCardsContainer.innerHTML = '';
        suggestedNewCardsContainer.appendChild(list);
    }

    function pollJobStatus(jobId, item, button, statusEl) {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`http://127.0.0.1:8000/job-status/${jobId}`);
                const result = await response.json();
                if (result.status === 'done') {
                    clearInterval(interval);
                    button.textContent = 'Done';
                    statusEl.textContent = 'Done';

                    const card = result.card || { ...item, image: `../aac_images/${item.category}/${item.word}.png` };
                    if (!aacData.some(c => c.category === card.category && c.word === card.word)) {
                        aacData.push({ ...card, image: `../aac_images/${card.category}/${card.word}.png` });
                        renderTabs();
                        renderCards(document.querySelector('.tab-btn.active').dataset.category);
                    }
                    showToast('Card added.', 'success');
                } else if (result.status === 'error') {
                    clearInterval(interval);
                    button.disabled = false;
                    button.textContent = 'Generate';
                    statusEl.textContent = 'Failed';
                    showToast('Failed to generate the card.', 'error');
                }
            } catch (error) {
                console.error('Error polling job status:', error);
            }
        }, 2500);
    }

    async function updateSelectionOnServer() {
        try {
            await fetch('http://127.0.0.1:8000/update-selection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ selection: selectedCards })
            });
        } catch (error) {
            console.error('Error updating selection on server:', error);
        }
    }

    function scheduleSelectionUpdate() {
        if (selectionUpdateTimer) {
            clearTimeout(selectionUpdateTimer);
        }
        selectionUpdateTimer = setTimeout(() => {
            selectionUpdateTimer = null;
            updateSelectionOnServer();
        }, 150);
    }

    function getCachedAudio(item) {
        if (!item?.category || !item?.word) return null;
        const key = `${item.category}|||${item.word}`;
        let audio = audioCache.get(key);
        if (!audio) {
            audio = new Audio(`../aac_audios/${item.category}/${item.word}.mp3`);
            audio.preload = 'auto';
            audioCache.set(key, audio);
        }
        return audio;
    }

    function prefetchAudio(items = []) {
        const limit = Math.min(items.length, MAX_AUDIO_PREFETCH);
        for (let i = 0; i < limit; i += 1) {
            getCachedAudio(items[i]);
        }
    }

    resetBtn.addEventListener('click', () => {
        selectedCards = [];
        renderSelectedCards();
        renderSuggestedCards();
        scheduleSelectionUpdate();
    });

    let mediaRecorder;
    let audioChunks = [];
    let stream;
    let isRecording = false;

    async function startRecording() {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                if (audioChunks.length === 0) {
                    alert('No recorded audio found.');
                    return;
                }

                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append('audio', audioBlob, 'recording.webm');

                try {
                    const response = await fetch('http://127.0.0.1:8000/upload-audio', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();
                    console.log('Upload complete:', result);
                } catch (error) {
                    console.error('Error uploading audio:', error);
                } finally {
                    audioChunks = [];
                }
            };

            mediaRecorder.start();
            isRecording = true;
            recordBtn.classList.add('recording');

        } catch (err) {
            console.error('Microphone access error:', err);
            alert('Microphone permission is required.');
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        isRecording = false;
        recordBtn.classList.remove('recording');
    }

    recordBtn.addEventListener('click', async (event) => {
        event.preventDefault();
        if (isRecording) {
            stopRecording();
        } else {
            await startRecording();
        }
    });

    setAuthMode('login');
    showAuthScreen();

});
