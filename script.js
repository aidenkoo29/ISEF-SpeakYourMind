document.addEventListener('DOMContentLoaded', () => {
    const cardContainer = document.getElementById('card-container');
    const selectedCardsContainer = document.getElementById('selected-cards');
    const suggestedCardsContainer = document.getElementById('suggested-cards');
    const tabsContainer = document.querySelector('.tabs');
    const resetBtn = document.getElementById('reset-btn');
    const augmentationBtn = document.getElementById('augmentation-btn');
    const augmentedPopup = document.getElementById('augmented-popup');
    const closeBtn = document.querySelector('.close-btn');
    const augmentedCardsPopupContainer = document.getElementById('augmented-cards-popup-container');

    let aacData = [];
    let selectedCards = [];

    // Fetch and parse CSV data
    fetch('aac_library.csv')
        .then(response => response.text())
        .then(data => {
            const rows = data.trim().split('\n').slice(1);
            aacData = rows.map(row => {
                const [category, word] = row.split(',');
                return { category, word, image: `aac_images/${category}/${word}.png` };
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
        card.innerHTML = `<img src="${item.image}" alt="${item.word}"><p>${item.word}</p>`;
        return card;
    }

    function addToSelected(item) {
        selectedCards.push(item);
        renderSelectedCards();
        playAudio(item);
    }

    function playAudio(item) {
        const audio = new Audio(`aac_audios/${item.category}/${item.word}.mp3`);
        audio.play();
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
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        augmentationBtn.appendChild(spinner);
        augmentationBtn.disabled = true;

        try {
            const response = await fetch('http://127.0.0.1:8000/augment-cards', { method: 'POST' });
            const result = await response.json();
            console.log("New cards received:", result.new_cards);

            if (result.new_cards && result.new_cards.length > 0) {
                result.new_cards.forEach(card => {
                    aacData.push({ ...card, image: `aac_images/${card.category}/${card.word}.png` });
                });
                renderTabs();
                renderCards(document.querySelector('.tab-btn.active').dataset.category);
                showAugmentedPopup(result.new_cards);
            }
        } catch (error) {
            console.error('Error augmenting cards:', error);
        } finally {
            augmentationBtn.removeChild(spinner);
            augmentationBtn.disabled = false;
        }
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

    window.addEventListener('click', (event) => {
        if (event.target === augmentedPopup) {
            augmentedPopup.style.display = 'none';
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

    const startRecordBtn = document.getElementById('start-record-btn');
    const stopRecordBtn = document.getElementById('stop-record-btn');

    let mediaRecorder;
    let audioChunks = [];
    let stream;

    startRecordBtn.addEventListener('click', async () => {
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
                }

                startRecordBtn.style.display = 'inline-block';
                stopRecordBtn.style.display = 'none';
                audioChunks = [];
            };

            mediaRecorder.start();
            startRecordBtn.style.display = 'none';
            stopRecordBtn.style.display = 'inline-block';

        } catch (err) {
            console.error('마이크 접근 오류:', err);
            alert('마이크 권한이 필요합니다.');
        }
    });

    stopRecordBtn.addEventListener('click', (event) => {
        event.preventDefault();
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            stream.getTracks().forEach(track => track.stop());
        }
    });

});