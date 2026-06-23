/* ============================================================
   作家语言指纹对比分析系统 — Frontend Application Logic
   ============================================================ */

// ---------- State ----------
const state = {
    sessionIdA: null,
    sessionIdB: null,
    resultA: null,
    resultB: null,
    comparison: null,
    textSampleA: '',
    textSampleB: '',
    appreciationText: '',
    wcModalTarget: '',  // 'a' or 'b'
};

// ---------- DOM References ----------
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ---------- Toast ----------
function showToast(msg, type = 'success') {
    const container = $('#toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3200);
}

// ---------- File Upload ----------
function setupFileUpload(which) {
    const btnFile = $(`#btnFile${which}`);
    const fileInput = $(`#fileInput${which}`);
    const fileName = $(`#fileName${which}`);
    const authorCard = $(`#authorCard${which}`);

    btnFile.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', async () => {
        const file = fileInput.files[0];
        if (!file) return;

        fileName.textContent = file.name;
        fileName.classList.add('uploaded');
        authorCard.classList.add('uploaded');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('author', which.toUpperCase());

        try {
            const res = await fetch('/api/upload', { method: 'POST', body: formData });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || '上传失败');
            }
            const data = await res.json();
            state[`sessionId${which}`] = data.session_id;
            showToast(`作家${which.toUpperCase()} 文件上传成功: ${file.name}`);
        } catch (e) {
            showToast(e.message, 'error');
            fileName.textContent = '未选择文件';
            fileName.classList.remove('uploaded');
            authorCard.classList.remove('uploaded');
        }
    });
}

setupFileUpload('A');
setupFileUpload('B');

// ---------- Analyze ----------
$('#btnAnalyze').addEventListener('click', async () => {
    const authorA = $('#authorNameA').value.trim();
    const authorB = $('#authorNameB').value.trim();

    if (!authorA || !authorB) { showToast('请填写两位作家的姓名', 'warning'); return; }
    if (!state.sessionIdA || !state.sessionIdB) { showToast('请为两位作家选择文本文件', 'warning'); return; }

    // Show progress
    $('#btnAnalyze').disabled = true;
    $('#btnExport').disabled = true;
    $('#btnAppreciation').disabled = true;
    $('#progressBar').style.display = 'flex';
    $('#resultSection').style.display = 'none';
    $('#comparisonSection').style.display = 'none';
    $('#appreciationSection').style.display = 'none';
    state.appreciationText = '';

    const stopwordsInput = $('#stopwordsInput').value.trim();
    const useDefault = $('#useDefaultStopwords').checked;

    try {
        const res = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id_a: state.sessionIdA,
                session_id_b: state.sessionIdB,
                author_a: authorA,
                author_b: authorB,
                use_default_stopwords: useDefault,
                custom_stopwords: stopwordsInput,
            }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '分析失败');
        }

        const data = await res.json();
        state.resultA = data.result_a;
        state.resultB = data.result_b;
        state.comparison = data.comparison;
        state.textSampleA = data.text_sample_a || '';
        state.textSampleB = data.text_sample_b || '';

        // Render results
        renderResult('A', state.resultA);
        renderResult('B', state.resultB);
        renderComparison(state.comparison);

        // Load word clouds
        loadWordCloud('A');
        loadWordCloud('B');

        // Show sections
        $('#resultSection').style.display = 'block';
        $('#comparisonSection').style.display = 'block';
        $('#btnExport').disabled = false;
        $('#btnAppreciation').disabled = false;

        showToast('分析完成！');
    } catch (e) {
        showToast(e.message, 'error');
    } finally {
        $('#btnAnalyze').disabled = false;
        $('#progressBar').style.display = 'none';
    }
});

// ---------- Render Results ----------
function renderResult(which, result) {
    const container = $(`#resultText${which}`);
    const topWords = result.top_words || [];
    const lines = [
        '─'.repeat(38),
        `  作家：${result.author_name}`,
        '─'.repeat(38),
        '',
        `  📊  总词数（全部词汇）：${(result.total_words || 0).toLocaleString()}`,
        `  📝  总句数：${(result.total_sentences || 0).toLocaleString()}`,
        `  📏  平均句长：${result.avg_sentence_length || 0} 词/句`,
        `  📈  独有内容词数：${(result.unique_content_words || 0).toLocaleString()}`,
        '',
        `  🏆  前 10 高频实词：`,
        '',
    ];

    if (topWords.length > 0) {
        topWords.forEach(([word, freq], idx) => {
            lines.push(`     ${String(idx + 1).padStart(2)}.  ${word}  ——  ${freq} 次`);
        });
    } else {
        lines.push('     （无内容词）');
    }
    lines.push('');
    lines.push('─'.repeat(38));

    container.textContent = lines.join('\n');
}

// ---------- Word Cloud ----------
function loadWordCloud(which) {
    const sid = state[`sessionId${which}`];
    if (!sid) return;

    const img = $(`#wcThumb${which}`);
    const placeholder = $(`#wcPlaceholder${which}`);
    const url = `/api/wordcloud/${sid}/${which.toLowerCase()}?w=350&h=230`;

    img.onload = () => {
        img.style.display = 'block';
        placeholder.style.display = 'none';
    };
    img.onerror = () => {
        img.style.display = 'none';
        placeholder.style.display = 'block';
        placeholder.textContent = '词云生成失败\n（可能缺少字体文件）';
    };
    img.src = url;

    // Click to open modal
    $(`#wcBox${which}`).onclick = () => openWcModal(which);
}

// ---------- Word Cloud Modal ----------
function openWcModal(which) {
    const sid = state[`sessionId${which}`];
    if (!sid) return;
    state.wcModalTarget = which;

    const imgUrl = `/api/wordcloud/${sid}/${which.toLowerCase()}?w=600&h=400`;
    $('#wcModalImage').src = imgUrl;
    const authorName = state[`result${which}`]?.author_name || `作家${which}`;
    $('#wcModalTitle').textContent = `📊 ${authorName} 的词云图（高清原图）`;
    $('#wcModal').style.display = 'flex';
}

$('#wcModalClose').addEventListener('click', () => { $('#wcModal').style.display = 'none'; });
$('#btnWcClose').addEventListener('click', () => { $('#wcModal').style.display = 'none'; });
$('#wcModal').addEventListener('click', (e) => {
    if (e.target === $('#wcModal')) $('#wcModal').style.display = 'none';
});

// Download word cloud
$('#btnDownloadWc').addEventListener('click', () => {
    const which = state.wcModalTarget;
    const sid = state[`sessionId${which}`];
    if (!sid) return;
    const dlUrl = `/api/export/wordcloud/${sid}/${which.toLowerCase()}?format=png`;
    window.open(dlUrl, '_blank');
});

// ---------- Render Comparison ----------
function renderComparison(comp) {
    const jaccard = comp.jaccard_similarity || 0;
    let jaccardLabel = '—';
    if (jaccard > 0) {
        jaccardLabel = jaccard > 0.5 ? '高度相似' : jaccard > 0.25 ? '中等相似' : '差异较大';
    }

    $('#compJaccard').textContent = jaccard > 0 ? `${jaccard.toFixed(4)} (${jaccardLabel})` : '—';
    $('#compShared').textContent = (comp.shared_top_words || []).length > 0
        ? comp.shared_top_words.join('、') : '（无）';
    $('#compUniqA').textContent = (comp.unique_a_count || 0).toLocaleString();
    $('#compUniqB').textContent = (comp.unique_b_count || 0).toLocaleString();
    $('#compSharedVocab').textContent = (comp.shared_vocabulary_count || 0).toLocaleString();
    $('#compUnion').textContent = (comp.total_vocabulary_union || 0).toLocaleString();

    const ratio = comp.sentence_length_ratio || 0;
    let ratioLabel = '—';
    if (ratio > 0) {
        ratioLabel = ratio > 1.05 ? 'A 更长' : ratio < 0.95 ? 'B 更长' : '基本一致';
    }
    $('#compSentRatio').textContent = ratio > 0 ? `${ratio.toFixed(2)} (${ratioLabel})` : '—';
}

// ---------- Article Appreciation ----------
$('#btnAppreciation').addEventListener('click', async () => {
    if (!state.resultA || !state.resultB) {
        showToast('请先完成文本分析', 'warning');
        return;
    }

    // Show appreciation section
    $('#appreciationSection').style.display = 'block';
    $('#appreciationText').textContent = '';
    $('#appreciationLoading').style.display = 'flex';
    $('#btnAppreciation').disabled = true;

    const apiKey = localStorage.getItem('deepseek_api_key') || '';

    try {
        const res = await fetch('/api/appreciation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                result_a: state.resultA,
                result_b: state.resultB,
                comparison: state.comparison,
                text_a_sample: state.textSampleA,
                text_b_sample: state.textSampleB,
                api_key: apiKey,
            }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || '赏析生成失败');
        }

        const data = await res.json();
        state.appreciationText = data.content;

        // Render markdown-like text
        renderAppreciation(data.content);
        showToast('文章赏析生成完成！');
    } catch (e) {
        $('#appreciationText').innerHTML = `<p style="color:var(--danger);padding:16px;">❌ ${e.message}</p>`;
        if (e.message.includes('API Key')) {
            showToast('请先在右上角设置中填入 DeepSeek API Key', 'warning');
        } else {
            showToast(e.message, 'error');
        }
    } finally {
        $('#appreciationLoading').style.display = 'none';
        $('#btnAppreciation').disabled = false;
    }
});

function renderAppreciation(text) {
    const container = $('#appreciationText');
    // Simple markdown rendering
    let html = text
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/^\- (.+)$/gm, '<li>$1</li>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');

    html = '<p>' + html + '</p>';
    html = html.replace(/<p><\/p>/g, '');
    container.innerHTML = html;
}

// ---------- Export Report ----------
$('#btnExport').addEventListener('click', async () => {
    if (!state.resultA || !state.resultB) {
        showToast('请先完成文本分析', 'warning');
        return;
    }

    try {
        const res = await fetch('/api/export/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                result_a: state.resultA,
                result_b: state.resultB,
                comparison: state.comparison,
                appreciation_text: state.appreciationText,
            }),
        });

        if (!res.ok) throw new Error('导出失败');

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const nameA = state.resultA.author_name || 'A';
        const nameB = state.resultB.author_name || 'B';
        a.download = `语言指纹对比_${nameA}_vs_${nameB}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('报告导出成功！');
    } catch (e) {
        showToast(e.message, 'error');
    }
});

// ---------- Export Appreciation ----------
$('#btnExportAppreciation').addEventListener('click', () => {
    if (!state.appreciationText) {
        showToast('暂无赏析内容可导出', 'warning');
        return;
    }
    const nameA = state.resultA?.author_name || 'A';
    const nameB = state.resultB?.author_name || 'B';
    const blob = new Blob([state.appreciationText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `文章赏析_${nameA}_vs_${nameB}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('赏析文本导出成功！');
});

// ---------- History ----------
async function loadHistory() {
    try {
        const res = await fetch('/api/history');
        if (!res.ok) throw new Error('加载失败');
        const entries = await res.json();
        renderHistory(entries);
    } catch (e) {
        console.error('加载历史记录失败:', e);
    }
}

function renderHistory(entries) {
    const list = $('#historyList');
    if (entries.length === 0) {
        list.innerHTML = '<li class="history-empty">暂无历史记录</li>';
        return;
    }
    list.innerHTML = entries.map(e => `
        <li data-id="${e.id}" onclick="restoreHistory(${e.id})">
            <span>${escHtml(e.author_a)} — ${escHtml(e.author_b)}</span>
            <span class="history-time">${(e.timestamp || '').slice(0, 16)}</span>
        </li>
    `).join('');
}

function escHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}

async function restoreHistory(id) {
    try {
        const res = await fetch(`/api/history/${id}`);
        if (!res.ok) throw new Error('恢复失败');
        const entry = await res.json();

        // Populate UI
        $('#authorNameA').value = entry.author_a;
        $('#authorNameB').value = entry.author_b;
        $('#btnExport').disabled = false;
        $('#btnAppreciation').disabled = false;

        if (entry.result_a) {
            state.resultA = entry.result_a;
            renderResult('A', entry.result_a);
        }
        if (entry.result_b) {
            state.resultB = entry.result_b;
            renderResult('B', entry.result_b);
        }
        if (entry.comparison) {
            state.comparison = entry.comparison;
            renderComparison(entry.comparison);
        }
        if (entry.appreciation_text) {
            state.appreciationText = entry.appreciation_text;
            $('#appreciationSection').style.display = 'block';
            renderAppreciation(entry.appreciation_text);
        }

        $('#resultSection').style.display = 'block';
        $('#comparisonSection').style.display = 'block';

        // Word clouds don't restore from history (no session_id)
        showToast('历史记录已恢复（词云需重新分析才能显示）');
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// New study
$('#btnNewStudy').addEventListener('click', async () => {
    // Save current to history if there's data
    if (state.resultA && state.resultB) {
        try {
            await fetch('/api/history', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    author_a: state.resultA.author_name || '',
                    author_b: state.resultB.author_name || '',
                    result_a_json: JSON.stringify(state.resultA),
                    result_b_json: JSON.stringify(state.resultB),
                    comparison_json: JSON.stringify(state.comparison || {}),
                    appreciation_text: state.appreciationText,
                }),
            });
            await loadHistory();
        } catch (e) {
            console.error('保存历史失败:', e);
        }
    }

    // Reset state
    state.sessionIdA = null;
    state.sessionIdB = null;
    state.resultA = null;
    state.resultB = null;
    state.comparison = null;
    state.textSampleA = '';
    state.textSampleB = '';
    state.appreciationText = '';

    // Reset UI
    $('#authorNameA').value = '';
    $('#authorNameB').value = '';
    $('#stopwordsInput').value = '';
    $('#fileNameA').textContent = '未选择文件';
    $('#fileNameA').classList.remove('uploaded');
    $('#fileNameB').textContent = '未选择文件';
    $('#fileNameB').classList.remove('uploaded');
    $('#authorCardA').classList.remove('uploaded');
    $('#authorCardB').classList.remove('uploaded');
    $('#fileInputA').value = '';
    $('#fileInputB').value = '';

    $('#resultSection').style.display = 'none';
    $('#comparisonSection').style.display = 'none';
    $('#appreciationSection').style.display = 'none';
    $('#progressBar').style.display = 'none';
    $('#btnExport').disabled = true;
    $('#btnAppreciation').disabled = true;

    $('#resultTextA').textContent = '';
    $('#resultTextB').textContent = '';
    $('#appreciationText').innerHTML = '';
    $('#wcThumbA').style.display = 'none';
    $('#wcPlaceholderA').style.display = 'block';
    $('#wcPlaceholderA').textContent = '词云图将在分析完成后显示\n点击查看大图';
    $('#wcThumbB').style.display = 'none';
    $('#wcPlaceholderB').style.display = 'block';
    $('#wcPlaceholderB').textContent = '词云图将在分析完成后显示\n点击查看大图';

    showToast('已清空界面，可以开始新的研究了');
});

// Clear history
$('#btnClearHistory').addEventListener('click', async () => {
    if (!confirm('确定要删除所有历史记录吗？此操作不可撤销。')) return;
    try {
        await fetch('/api/history', { method: 'DELETE' });
        renderHistory([]);
        showToast('历史记录已清除');
    } catch (e) {
        showToast('清除失败', 'error');
    }
});

// ---------- Feature Intro Modal ----------
$('#btnIntro').addEventListener('click', () => { $('#introModal').style.display = 'flex'; });
$('#introModalClose').addEventListener('click', () => { $('#introModal').style.display = 'none'; });
$('#btnIntroClose').addEventListener('click', () => {
    if ($('#hideIntroNext').checked) {
        localStorage.setItem('hide_intro', 'true');
    }
    $('#introModal').style.display = 'none';
});
$('#introModal').addEventListener('click', (e) => {
    if (e.target === $('#introModal')) $('#introModal').style.display = 'none';
});

// ---------- Settings Modal ----------
$('#btnSettings').addEventListener('click', () => {
    const savedKey = localStorage.getItem('deepseek_api_key') || '';
    $('#apiKeyInput').value = savedKey;
    $('#settingsModal').style.display = 'flex';
});
$('#settingsModalClose').addEventListener('click', () => { $('#settingsModal').style.display = 'none'; });
$('#settingsModal').addEventListener('click', (e) => {
    if (e.target === $('#settingsModal')) $('#settingsModal').style.display = 'none';
});
$('#btnSaveSettings').addEventListener('click', () => {
    const key = $('#apiKeyInput').value.trim();
    localStorage.setItem('deepseek_api_key', key);
    $('#settingsModal').style.display = 'none';
    showToast(key ? 'API Key 已保存到浏览器' : 'API Key 已清除');
});

// ---------- Keyboard shortcuts ----------
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        $$('.modal-overlay').forEach(m => m.style.display = 'none');
    }
});

// ---------- Init ----------
loadHistory();

// Show intro on first visit
if (!localStorage.getItem('hide_intro')) {
    $('#introModal').style.display = 'flex';
}
