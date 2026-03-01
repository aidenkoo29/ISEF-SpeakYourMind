document.addEventListener('DOMContentLoaded', () => {
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
    const communityBtn = document.getElementById('community-btn');
    const communityPopup = document.getElementById('community-popup');
    const communityCloseBtn = document.getElementById('community-close-btn');
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
    const shareCardSelect = document.getElementById('share-card-select');
    const shareTimeInput = document.getElementById('share-time');
    const sharePlaceInput = document.getElementById('share-place');
    const shareOccasionInput = document.getElementById('share-occasion');
    const shareTagsInput = document.getElementById('share-tags');
    const shareSubmitBtn = document.getElementById('share-submit-btn');

    let aacData = [];
    let selectedCards = [];

    // Fetch and parse CSV data
    fetch('../data/aac_library.csv')
        .then(response => response.text())
        .then(data => {
            const rows = data.trim().split('\n').slice(1);
            aacData = rows.map(row => {
                const [category, word] = row.split(',');
                return { category, word, image: `../aac_images/${category}/${word}.png` };
            });
            renderTabs();
            renderCards('All');
        });

    function renderTabs() {
    const categories = ['All', '즐겨찾기', ...new Set(aacData.map(item => item.category))];
    tabsContainer.innerHTML = '';
    categories.forEach(category => {
        const tabBtn = document.createElement('button');
        tabBtn.className = 'tab-btn';
        tabBtn.textContent = category === 'All' ? '전체' : category;
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
        const filteredData = category === 'All' ? aacData : aacData.filter(item => item.category === category);
        filteredData.forEach(item => {
            const card = createCard(item);
            card.addEventListener('click', () => addToSelected(item));
            cardContainer.appendChild(card);
        });
    }

    function createCard(item) {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `<img src="${normalizeAssetPath(item.image)}" alt="${item.word}"><p>${item.word}</p>`;
        return card;
    }

    function addToSelected(item) {
        selectedCards.push(item);
        renderSelectedCards();
        playAudio(item);
    }

    function playAudio(item) {
        const audio = new Audio(`../aac_audios/${item.category}/${item.word}.mp3`);
        audio.play();
    }

    function playAudioUrl(url) {
        if (!url) {
            showToast('오디오 경로가 없습니다.', 'error');
            return;
        }
        const audio = new Audio(normalizeAssetPath(url));
        audio.play();
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
        updateSelectionOnServer();
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
        if (event.target === communityPopup) {
            communityPopup.style.display = 'none';
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
            communityResults.innerHTML = '<p>결과가 없습니다.</p>';
            return;
        }

        cards.forEach(card => {
            const wrapper = document.createElement('div');
            wrapper.className = 'community-card';

            const tags = (card.tags || []).join(', ');
            const context = [card.context_time, card.context_place, card.context_occasion].filter(Boolean).join(' · ');

            wrapper.innerHTML = `
                <div class="community-card-meta">
                    <strong>${card.name}</strong>
                    <span>${card.category || ''}</span>
                </div>
                <div class="community-card-info">
                    ${tags ? `<span>태그: ${tags}</span>` : ''}
                    ${context ? `<span>상황: ${context}</span>` : ''}
                </div>
                <div class="community-card-actions">
                    <button type="button" data-card-id="${card.id}">자세히</button>
                </div>
            `;

            const detailBtn = wrapper.querySelector('button[data-card-id]');
            detailBtn.addEventListener('click', () => openCommunityDetail(card.id));

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
            showToast('커뮤니티 검색에 실패했습니다.', 'error');
        }
    }

    async function openCommunityDetail(cardId) {
        if (!cardId) return;
        try {
            const response = await fetch(`http://127.0.0.1:8000/community/card/${cardId}`);
            const result = await response.json();
            if (result.error || !result.card) {
                showToast('카드를 찾을 수 없습니다.', 'error');
                return;
            }

            const card = result.card;
            communityDetailTitle.textContent = card.name || '';

            const tags = (card.tags || []).join(', ');
            const contextLines = [
                card.context_time ? `시간: ${card.context_time}` : '',
                card.context_place ? `장소: ${card.context_place}` : '',
                card.context_occasion ? `상황: ${card.context_occasion}` : '',
            ].filter(Boolean);

            communityDetailBody.innerHTML = `
                ${card.image ? `<img src="${normalizeAssetPath(card.image)}" alt="${card.name || ''}">` : ''}
                <p>카테고리: ${card.category || ''}</p>
                ${tags ? `<p>태그: ${tags}</p>` : ''}
                ${contextLines.map(line => `<p>${line}</p>`).join('')}
            `;

            communityDetailAudioBtn.onclick = () => playAudioUrl(card.audio);
            communityDetailCopyBtn.onclick = () => copyCommunityCard(card.id);
            communityDetailPopup.style.display = 'flex';
        } catch (error) {
            console.error('Error opening community detail:', error);
            showToast('카드 상세 정보를 불러오지 못했습니다.', 'error');
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
                showToast('카드 복사에 실패했습니다.', 'error');
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
            showToast('내 라이브러리에 추가되었습니다.', 'success');
        } catch (error) {
            console.error('Error copying community card:', error);
            showToast('카드 복사에 실패했습니다.', 'error');
        }
    }

    function populateShareSelect() {
        shareCardSelect.innerHTML = '';
        const sorted = [...aacData].sort((a, b) => a.word.localeCompare(b.word, 'ko'));
        sorted.forEach(item => {
            const option = document.createElement('option');
            option.value = `${item.category}|||${item.word}`;
            option.textContent = `${item.word} (${item.category})`;
            shareCardSelect.appendChild(option);
        });
    }

    function openSharePopup() {
        populateShareSelect();
        shareTimeInput.value = '';
        sharePlaceInput.value = '';
        shareOccasionInput.value = '';
        shareTagsInput.value = '';
        communitySharePopup.style.display = 'flex';
    }

    async function submitShare() {
        const selectedValue = shareCardSelect.value;
        if (!selectedValue) {
            showToast('공유할 카드를 선택해주세요.', 'error');
            return;
        }
        const [category, word] = selectedValue.split('|||');
        const card = aacData.find(item => item.category === category && item.word === word);
        if (!card) {
            showToast('선택한 카드를 찾을 수 없습니다.', 'error');
            return;
        }

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
            const response = await fetch('http://127.0.0.1:8000/community/share', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (!result.card) {
                showToast('공유에 실패했습니다.', 'error');
                return;
            }
            communitySharePopup.style.display = 'none';
            await loadCommunityResults(communitySearchInput.value.trim());
            showToast('커뮤니티에 공유했습니다.', 'success');
        } catch (error) {
            console.error('Error sharing community card:', error);
            showToast('공유에 실패했습니다.', 'error');
        }
    }

    communityBtn.addEventListener('click', async () => {
        communityPopup.style.display = 'flex';
        await loadCommunityResults(communitySearchInput.value.trim());
    });

    communityCloseBtn.addEventListener('click', () => {
        communityPopup.style.display = 'none';
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
            showToast('추천 카드를 불러오지 못했습니다.', 'error');
        }
    }

    function renderNewCardSuggestions(suggestions) {
        if (suggestions.length === 0) {
            suggestedNewCardsContainer.innerHTML = '<p>새로 추천할 카드가 없습니다.</p>';
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
            button.textContent = exists ? '이미 추가됨' : '생성하기';
            button.disabled = exists;

            const status = document.createElement('span');

            button.addEventListener('click', async () => {
                button.disabled = true;
                button.textContent = '생성중...';
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
                    button.textContent = '생성하기';
                    showToast('카드 생성에 실패했습니다.', 'error');
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
                    button.textContent = '완료';
                    statusEl.textContent = '완료';

                    const card = result.card || { ...item, image: `../aac_images/${item.category}/${item.word}.png` };
                    if (!aacData.some(c => c.category === card.category && c.word === card.word)) {
                        aacData.push({ ...card, image: `../aac_images/${card.category}/${card.word}.png` });
                        renderTabs();
                        renderCards(document.querySelector('.tab-btn.active').dataset.category);
                    }
                    showToast('카드가 추가되었습니다.', 'success');
                } else if (result.status === 'error') {
                    clearInterval(interval);
                    button.disabled = false;
                    button.textContent = '생성하기';
                    statusEl.textContent = '실패';
                    showToast('카드 생성에 실패했습니다.', 'error');
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

    resetBtn.addEventListener('click', () => {
        selectedCards = [];
        renderSelectedCards();
        renderSuggestedCards();
        updateSelectionOnServer();
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
                    alert("녹음된 오디오가 없습니다.");
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
            console.error('마이크 접근 오류:', err);
            alert('마이크 권한이 필요합니다.');
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

});
