const $ = (id) => document.getElementById(id);
const escapeHTML = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = {token:'', active:null, source:null, article:null, busy:false, timer:null, crop:null, editFigure:null, dirty:false, metadataDirty:false, figuresDirty:false, reviewDirty:false, configured:false, desktop:false};
state.feedSelected=new Set();
let toastTimer;
function toast(message, error=false) { $('toast').textContent=message; $('toast').classList.toggle('error',error); $('toast').hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('toast').hidden=true,error?9000:4500); }
function guarded(fn) { return async (...args)=>{try{await fn(...args);}catch(e){toast(e.message,true);}}; }
async function request(path, body, raw=false) {
  const options = path==='/api/desktop/action'?{}:{signal:AbortSignal.timeout(60000)};
  if(body!==undefined){options.method='POST';options.headers={'X-Studio-Token':state.token,'Content-Type':raw?'application/octet-stream':'application/json'};options.body=raw?body:JSON.stringify(body);}
  const response=await fetch(path,options);
  const result=await response.json();
  if(!response.ok) throw new Error(result.error||'请求未完成');
  return result;
}
const endpoint = (action) => `/api/jobs/${state.active}/${action}`;
const asset = (name) => endpoint('asset')+'?name='+encodeURIComponent(name)+'&v='+Date.now();
function settings() { return {base_url:$('baseUrl').value.trim(),model:$('modelId').value.trim(),api_key:state.desktop?'':$('apiKey').value,vision:$('vision').checked,output_tokens:Number($('outputTokens').value)||0,thinking:$('thinkingMode').value}; }
async function refreshModels(){
  const s=await request('/api/session');state.token=s.token;state.desktop=Boolean(s.desktop);state.configured=s.configured;state.profileId=s.active_profile||'';
  $('openData').hidden=!state.desktop;$('rememberRow').hidden=!state.desktop;
  $('modelProfiles').innerHTML='<option value="">新增模型配置</option>'+(s.profiles||[]).map(p=>`<option value="${escapeHTML(p.id)}">${escapeHTML(p.name||p.model)}</option>`).join('');
  $('modelProfiles').value=state.profileId;const selected=(s.profiles||[]).find(p=>p.id===state.profileId);
  $('profileName').value=selected?.name||'';$('baseUrl').value=s.base_url;$('modelId').value=s.model;
  $('outputTokens').value=s.output_tokens||'';$('thinkingMode').value=s.thinking||'high';
  $('rememberModels').checked=s.profiles?.length?Boolean(s.remember_models):true;
  $('apiKey').value='';$('apiKey').placeholder=s.configured?'已设置（不回显）；留空沿用此配置的密钥':'填写服务商提供的密钥';
  $('deleteModel').disabled=!state.profileId;$('modelBadge').textContent=s.model||'尚未配置模型';
  if(s.model_warning)toast(s.model_warning,true);
}
function newModel(){state.profileId='';$('modelProfiles').value='';$('profileName').value='';$('baseUrl').value='https://api.deepseek.com';$('modelId').value='deepseek-flash';$('apiKey').value='';$('apiKey').placeholder='新配置需要独立填写密钥';$('outputTokens').value='';$('thinkingMode').value='high';$('deleteModel').disabled=true;$('profileName').focus();}
function options() { return {...settings(),style:$('style').value,auto_figures:$('autoFigures').checked,length:Number($('length').value),brief:$('brief').value,figure_ids:state.source?.figures.filter(f=>f.selected).map(f=>f.id)||[]}; }
function showTab(name) {if(name==='review'&&state.active)guarded(refreshWechatReview)(); document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));document.querySelectorAll('.tab-panel').forEach(p=>p.hidden=p.id!=='tab-'+name); }
function busy(value) {state.busy=value;document.querySelectorAll('#tab-review input,#tab-review select,#tab-review textarea,#tab-review button').forEach(e=>e.disabled=value);if(!value&&state.wechatReview)updateReviewButtons();document.querySelectorAll('#draftEditor input,#draftEditor textarea,#draftEditor button,#figureGallery input,#figureGallery textarea,#figureGallery button,#paperInfoPanel input,#paperInfoPanel textarea,#paperInfoPanel button,#repairCrops,#projectMediaPanel button,#projectVideos input,#materialsPanel button,#materialsPanel input,#materialsPanel select').forEach(el=>el.disabled=value);$('generate').disabled=value||!state.source?.can_generate;$('saveDraft').disabled=value||!state.article;$('saveFigures').disabled=value;$('saveCrop').disabled=value||!state.crop;['exportZip','exportMd','copyHtml','skillFormat'].forEach(id=>$(id).disabled=value||!state.article);}
function downloadText(text, filename, type='text/plain;charset=utf-8') {const url=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);}
function approveNavigation() {return !(state.dirty||state.metadataDirty||state.figuresDirty||state.reviewDirty)||confirm('还有未保存的修改，离开会丢失这些修改。确定离开吗？');}

async function refreshHistory() {
  state.jobs=await request('/api/jobs');renderLibrary();
}
function renderLibrary(){
  const search=$('librarySearch').value.trim().toLowerCase();
  const jobs=(state.jobs||[]).filter(j=>Boolean(j.trashed)===Boolean(state.showTrash)&&(!search||((j.display_name||'')+' '+j.title).toLowerCase().includes(search)));
  $('jobCount').textContent=(state.jobs||[]).filter(j=>!j.trashed).length;
  $('showTrash').classList.toggle('active',Boolean(state.showTrash));
  $('history').innerHTML=jobs.length?jobs.map(j=>`<div class="library-entry"><button class="history-item ${j.id===state.active?'active':''}" ${j.trashed?'disabled':''} data-job="${j.id}" title="${escapeHTML(j.title)}"><strong>${j.pinned?'★ ':''}${escapeHTML(j.display_name||j.title)}</strong><small>${escapeHTML({ready:'已保存',running:'处理中',queued:'等待处理',error:'需要检查'}[j.status]||j.status)} · ${new Date(j.created_at*1000).toLocaleDateString('zh-CN')}</small></button>${j.trashed?`<button class="text-button" data-restore="${j.id}">恢复作品</button>`:''}</div>`).join(''):'<p class="muted">'+(state.showTrash?'回收站为空。':'没有匹配的作品。')+'</p>';
  const current=state.jobs?.find(j=>j.id===state.active);$('pinJob').textContent=current?.pinned?'取消置顶':'置顶';
}
$('librarySearch').oninput=renderLibrary;
$('showLibrary').onclick=()=>{state.showTrash=false;renderLibrary();};
$('showTrash').onclick=()=>{state.showTrash=true;renderLibrary();};
$('history').addEventListener('click',guarded(async e=>{const b=e.target.closest('[data-restore]');if(b){await request(`/api/jobs/${b.dataset.restore}/library`,{trashed:false});await refreshHistory();toast('作品已恢复。');}}));
$('renameJob').onclick=guarded(async()=>{const j=state.jobs.find(j=>j.id===state.active);const name=prompt('作品名称（不改动论文原始标题；留空恢复原题）',j.display_name||j.title);if(name!==null){await request(endpoint('library'),{display_name:name});await refreshHistory();}});
$('pinJob').onclick=guarded(async()=>{const j=state.jobs.find(j=>j.id===state.active);await request(endpoint('library'),{pinned:!j.pinned});await refreshHistory();});
$('trashJob').onclick=guarded(async()=>{if(state.busy)throw new Error('请等待当前任务完成。');if(!approveNavigation()||!confirm('移入回收站？原文、草稿和素材保留，可随时恢复。'))return;await request(endpoint('library'),{trashed:true});state.dirty=state.metadataDirty=state.figuresDirty=state.reviewDirty=false;$('newPaper').click();toast('已移入回收站，可从侧边栏恢复。');});
$('refreshIdentity').onclick=guarded(async()=>{await savePaperInfo();await saveDraft(false);await saveFigures(false);await request(endpoint('refresh-identity'),{});await watchJob(state.active);});
async function openJob(id) {
  clearTimeout(state.timer);state.active=id;state.article=null;state.source=null;state.dirty=false;state.metadataDirty=false;state.figuresDirty=false;state.reviewDirty=false;state.wechatReview=null;
  $('workspace').hidden=true;$('welcome').hidden=false;
  await refreshHistory(); await watchJob(id);
}
async function watchJob(id) {
  if(id!==state.active) return;
  const task=await request(`/api/jobs/${id}/status`);
  if(id!==state.active) return;
  const running=['running','queued'].includes(task.status);busy(running);
  $('taskBanner').hidden=!running;$('cancelTask').hidden=String(task.operation||'').startsWith('wechat');$('taskTitle').textContent=String(task.operation||'').startsWith('wechat')?'正在提交与核对公众号草稿':task.operation==='generate'?'正在研读与写作':task.operation==='skill'?'正在排版':'正在整理论文材料';$('taskMessage').textContent=task.message;
  if(running){state.timer=setTimeout(()=>guarded(()=>watchJob(id))(),2000);return;}
  if(task.status==='error') toast(task.message,true);
  await loadDocument(id);
  await refreshHistory();
  if(task.operation?.startsWith('wechat'))await refreshWechatReview();
  if(task.operation==='direct-draft'&&task.status==='ready'){showTab('review');toast(task.message||'已处理，查看公众号草稿回执。');}
  if(task.operation==='skill'&&task.status==='ready') {
    $('theme').value='baoyu';renderPreview();
    state.reviewDirty=false;await refreshWechatReview();
    toast('宝玉排版已应用。请前往“人工审核与提交”，审核后正文、图片和封面会自动上传为草稿。');
  }
}
async function loadDocument(id) {
  let source;try{source=await request(`/api/jobs/${id}/source`);}catch{return;}
  if(id!==state.active)return;state.source=source;
  $('welcome').hidden=true;$('workspace').hidden=false;
  $('paperTitle').textContent=source.title;
  $('sourceMeta').textContent=[source.arxiv_id?'arXiv '+source.arxiv_id:'本地 PDF',`${source.pages.length} 页`,`${source.figures.length} 张候选配图`,`${source.text_chars.toLocaleString()} 字符原文`].join('  /  ');
  $('openPdf').href=asset('source.pdf');
  const warnings=[...source.warnings,source.metadata_note].filter(Boolean);$('sourceWarnings').hidden=!warnings.length;$('sourceWarnings').textContent=warnings.join(' ');
  $('pageSelect').innerHTML=source.pages.map(p=>`<option value="${p.number}">第 ${p.number} 页</option>`).join('');showPage();renderFigures();await renderProjectMedia();await renderMaterials();
  try{state.article=await request(endpoint('article'));const review=await request(endpoint('wechat'));$('theme').value=review.options.theme||'ink';}catch{state.article=null;}
  renderPaperInfo();if(state.article){renderEditor();await renderAudit();renderPreview();}else{renderEmpty();}
  busy(false);
}
function renderPaperInfo(){
  const info=state.source.publication_info||state.source.paper_info||{title:state.source.title,authors:state.source.authors,paper_url:state.source.source_url};
  document.querySelectorAll('[data-paper-info]').forEach(el=>{const value=info[el.dataset.paperInfo];el.value=Array.isArray(value)?value.join('\n'):value||'';});
  state.metadataDirty=false;$('savePaperInfo').textContent='保存论文资料';
}
async function savePaperInfo(showToast=false){
  if(!state.metadataDirty)return;
  const info={};document.querySelectorAll('[data-paper-info]').forEach(el=>{const key=el.dataset.paperInfo;info[key]=['authors','affiliations'].includes(key)?el.value.split('\n').map(v=>v.trim()).filter(Boolean):el.value.trim();});
  info.verified_on=new Date().toLocaleDateString('en-CA');
  state.source.paper_info=await request(endpoint('paper-info'),info);state.source.publication_info=state.source.paper_info;
  if(info.title){state.source.title=info.title;$('paperTitle').textContent=info.title;}await refreshHistory();
  state.metadataDirty=false;$('savePaperInfo').textContent='已保存';renderPreview();if(state.article)await renderAudit();if(showToast)toast('论文信息卡已更新。');
}
function tableEditor(t,i,j){return `<div class="draft-result-table"><label>图表位置（跟在本章第几段后）<input type="number" min="1" data-table-position="${i}:${j}" value="${t.after_paragraph||state.article.sections[i].paragraphs.length||1}"></label><label>结果摘要标题<input data-table-field="${i}:${j}:title" value="${escapeHTML(t.title||'')}"></label><label>表头（用 Tab 分隔各列）<input data-table-columns="${i}:${j}" value="${escapeHTML(t.columns.join('\t'))}"></label><label>数据（每行一项，用 Tab 分隔各列；可从表格粘贴）<textarea data-table-rows="${i}:${j}">${escapeHTML(t.rows.map(r=>r.join('\t')).join('\n'))}</textarea></label><label>来源表号<input data-table-field="${i}:${j}:source_label" value="${escapeHTML(t.source_label||'')}"></label><label>评测条件与单位<input data-table-field="${i}:${j}:note" value="${escapeHTML(t.note||'')}"></label></div>`;}
function renderEmpty(){
  $('draftEditor').innerHTML='<div class="draft-empty"><span>Aa</span><h3>先读懂，再写好。</h3><p>确认配图后生成文章，或导出完整提示词，<br>用自己的模型写作，再导入成稿 JSON。</p><button class="secondary" data-configure>配置写作模型</button></div>';
  $('draftStats').textContent='等待成稿';$('previewEmpty').hidden=false;$('preview').removeAttribute('src');$('auditContent').innerHTML='<p class="muted">成稿后显示证据卡片。</p>';$('issueCount').textContent='';
}
function renderPreview(){if(state.article){$('preview').src=endpoint('preview')+'?theme='+$('theme').value+'&v='+Date.now();$('previewEmpty').hidden=true;}}
function renderEditor(){
  const a=state.article;
  $('draftEditor').innerHTML=`<label>推文主标题<textarea class="draft-title" data-field="title">${escapeHTML(a.title)}</textarea></label>${a.title_options?.length?`<div class="title-options">${a.title_options.map((t,i)=>`<button data-title-option="${i}">${escapeHTML(t)}</button>`).join('')}</div>`:''}<label>摘要<textarea data-field="digest">${escapeHTML(a.digest||'')}</textarea></label><label>导语<textarea data-field="lead">${escapeHTML(a.lead||'')}</textarea></label>`+
    a.sections.map((s,i)=>`<section class="draft-section"><p class="section-kind">${String(i+1).padStart(2,'0')} / ${escapeHTML(s.kind||'SECTION')}</p><input aria-label="章节标题" data-section-title="${i}" value="${escapeHTML(s.heading)}">${s.paragraphs.map((p,j)=>`<textarea aria-label="第 ${i+1} 章第 ${j+1} 段" data-paragraph="${i}:${j}">${escapeHTML(p.text)}</textarea><div class="source-ref">原文页码：${escapeHTML((p.pages||[]).join(', ')||'待补充')}</div>`).join('')}${(s.tables||[]).map((t,j)=>tableEditor(t,i,j)).join('')}${(s.figures||[]).map((f,j)=>`<div class="draft-figure-note">原图 ${escapeHTML(f.id)}<label>图表位置（跟在本章第几段后）<input type="number" min="1" data-fig-position="${i}:${j}" value="${f.after_paragraph||s.paragraphs.length||1}"></label><label>中文图注<input data-fig-caption="${i}:${j}" value="${escapeHTML(f.caption||'')}"></label><label>读图说明<textarea data-fig-explanation="${i}:${j}">${escapeHTML(f.explanation||'')}</textarea></label></div>`).join('')}</section>`).join('')+
    `<label>结尾要点（每行一条）<textarea data-field="takeaways">${escapeHTML((a.takeaways||[]).join('\n'))}</textarea></label>`;
  $('draftStats').textContent=a.sections.reduce((n,s)=>n+s.paragraphs.reduce((m,p)=>m+p.text.length,0),0).toLocaleString()+' 字';
}
function collectDraft(){
  if(!state.article)return null;
  const a=structuredClone(state.article);
  document.querySelectorAll('[data-field]').forEach(el=>a[el.dataset.field]=el.dataset.field==='takeaways'?el.value.split('\n').filter(Boolean):el.value);
  document.querySelectorAll('[data-section-title]').forEach(el=>a.sections[Number(el.dataset.sectionTitle)].heading=el.value);
  document.querySelectorAll('[data-paragraph]').forEach(el=>{const[i,j]=el.dataset.paragraph.split(':').map(Number);a.sections[i].paragraphs[j].text=el.value;});
  for(const [attr,key] of [['figCaption','caption'],['figExplanation','explanation']]) document.querySelectorAll(`[data-${attr==='figCaption'?'fig-caption':'fig-explanation'}]`).forEach(el=>{const[i,j]=el.dataset[attr].split(':').map(Number);a.sections[i].figures[j][key]=el.value;});
  document.querySelectorAll('[data-table-field]').forEach(el=>{const[i,j,key]=el.dataset.tableField.split(':');a.sections[i].tables[j][key]=el.value;});
  document.querySelectorAll('[data-table-columns]').forEach(el=>{const[i,j]=el.dataset.tableColumns.split(':');a.sections[i].tables[j].columns=el.value.split('\t').map(v=>v.trim());});
  document.querySelectorAll('[data-table-rows]').forEach(el=>{const[i,j]=el.dataset.tableRows.split(':');a.sections[i].tables[j].rows=el.value.split('\n').filter(v=>v.trim()).map(row=>row.split('\t').map(v=>v.trim()));});
  for(const kind of ['fig','table'])document.querySelectorAll(`[data-${kind}-position]`).forEach(el=>{const[i,j]=el.dataset[kind+'Position'].split(':');a.sections[i][kind==='fig'?'figures':'tables'][j].after_paragraph=Number(el.value);});
  if(state.dirty)a.manual_edit=true;
  return a;
}
async function saveDraft(showToast=true){await savePaperInfo();if(!state.article)return;const article=collectDraft();await request(endpoint('article'),article);state.article=await request(endpoint('article'));state.dirty=false;$('saveDraft').textContent='已保存';renderPreview();await renderAudit();if(showToast)toast('修改已保存，预览和证据提醒已更新。');}
async function renderAudit(){
  const audit=await request(endpoint('audit'));$('issueCount').textContent=audit.issues.length?audit.issues.length+' 项提醒':'';
  $('auditContent').innerHTML=`<p class="audit-note">${escapeHTML(audit.note)}</p>${state.article.manual_edit?'<p class="notice">正文经过人工编辑，请重新核对段落与原有证据卡是否仍然一致。</p>':''}`+(audit.figure_coverage?.missing||[]).map(m=>`<p class="notice">配图尚待补全：${escapeHTML(m)}</p>`).join('')+audit.issues.map(i=>`<p class="audit-note">↗ ${escapeHTML(i.message)}</p>`).join('')+(state.article.review_notes||[]).map(t=>`<p class="audit-note">编辑复核：${escapeHTML(t)}</p>`).join('')+audit.evidence.map(e=>`<article class="evidence-item ${e.quote_found?'match':''}"><span>${e.quote_found?'已定位原文引句 · 仍需核查解读':'引句未匹配，请人工核对'} / p. ${escapeHTML(e.page)}</span><h3>${escapeHTML(e.claim)}</h3><blockquote>${escapeHTML(e.quote)}</blockquote><button class="text-button" data-source-page="${Number(e.page)||1}">查看原文页 ↗</button></article>`).join('');
}
function renderFigures(){
  $('figureCount').textContent=state.source.figures.length;
  const target=$('materialTarget').value;
  $('materialTarget').innerHTML='<option value="">新增候选配图</option>'+state.source.figures.map(f=>`<option value="${f.id}">替换 ${f.id} · ${escapeHTML(f.caption.slice(0,60))}</option>`).join('');
  $('materialTarget').value=target;
  $('figureGallery').innerHTML=state.source.figures.length?state.source.figures.map(f=>`<article class="figure-card" data-figure="${f.id}"><header><span>${f.id} · ${f.kind==='project_image'?'作者项目页':f.origin==='local_image'?'本机导入'+(f.page?' · p. '+f.page:''):f.origin==='pdf_embedded'?'内嵌原图 · p. '+f.page:'p. '+f.page}</span><label><input type="checkbox" data-selected ${f.selected?'checked':''}>用于写稿</label></header><img src="${asset(f.image)}" alt="${escapeHTML(f.caption)}" loading="lazy"><p class="crop-status">${f.crop_status==='page_fallback'?'保留整页 · 请核对或手动框选':f.reviewed?'已核对配图':f.origin?'导入素材 · 请核对图例、标注与完整性':'候选裁剪 · 请核对表头、行列与脚注'}</p><textarea aria-label="原图图注" data-caption>${escapeHTML(f.caption)}</textarea><footer><label><input type="checkbox" data-reviewed ${f.reviewed?'checked':''}>已核对</label>${f.origin?`<button class="text-button" data-replace-figure="${f.id}">替换图片 ↗</button>${f.page?`<button class="text-button" data-open-page="${f.page}">对照原页 ↗</button>`:""}`:f.kind==='project_image'?`<a class="text-button" target="_blank" rel="noopener" href="${escapeHTML(f.project_url)}">素材来源 ↗</a>`:`<button class="text-button" data-view-figure="${f.id}">原页 / 重裁 ↗</button>`}</footer></article>`).join(''):'<p class="muted">没有识别到标准图注。请在左侧原文页拖选需要的图表。</p>';
}
async function saveFigures(showToast=true){
  const figures=[...document.querySelectorAll('[data-figure]')].map(card=>({id:card.dataset.figure,selected:card.querySelector('[data-selected]').checked,reviewed:card.querySelector('[data-reviewed]').checked,caption:card.querySelector('[data-caption]').value}));
  if(figures.filter(f=>f.selected).length>12)throw new Error('生成时最多选择 12 张原图，请减少勾选。');
  const media=[...document.querySelectorAll('[data-project-video]')].map(card=>({id:card.dataset.projectVideo,selected:card.querySelector('[data-video-selected]').checked,caption:card.querySelector('[data-video-caption]').value}));state.source=await request(endpoint('figures'),{figures,media});state.figuresDirty=false;if(showToast)toast('配图选择已保存。');
}
async function renderProjectMedia(){
  const catalog=await request(endpoint('project-media'));
  const saved=[...state.source.figures,...(state.source.project_media||[])].map(f=>f.source_url);
  $('projectMediaList').innerHTML=(catalog.note?`<p class="muted">${escapeHTML(catalog.note)}</p>`:'')+(catalog.items||[]).map(m=>`<div class="media-candidate"><span>${m.kind==='video'?'视频':'图片'} · ${escapeHTML(m.label)}<small>${escapeHTML(m.url)}</small></span><button class="secondary" data-import-media="${m.id}" ${saved.includes(m.url)?'disabled':''}>${saved.includes(m.url)?'已下载':'下载到本机'}</button></div>`).join('');
  $('projectVideos').innerHTML=(state.source.project_media||[]).map(m=>`<div class="media-candidate" data-project-video="${m.id}"><label><input type="checkbox" data-video-selected ${m.selected?'checked':''}> 加入图文包<input data-video-caption value="${escapeHTML(m.caption)}"><small>原视频已下载 · ${(m.bytes/1024/1024).toFixed(1)} MB</small></label><video controls preload="metadata" src="${asset(m.file)}" style="max-width:300px;width:100%"></video></div>`).join('');
}
$('scanProjectMedia').onclick=guarded(async()=>{await saveDraft(false);await saveFigures(false);await request(endpoint('scan-media'),{});await watchJob(state.active);showTab('figures');});
$('projectMediaList').addEventListener('click',guarded(async e=>{const b=e.target.closest('[data-import-media]');if(!b)return;await saveDraft(false);await saveFigures(false);await request(endpoint('import-media'),{id:b.dataset.importMedia});await watchJob(state.active);showTab('figures');}));
function showPage(number){
  if(number)$('pageSelect').value=String(number);
  const page=state.source.pages[Number($('pageSelect').value)-1];if(!page)return;
  $('sourcePage').src=asset(page.image);$('sourceText').textContent=page.text;resetCrop();
}
function resetCrop(){state.crop=null;state.editFigure=null;$('cropSelection').hidden=true;$('saveCrop').disabled=true;$('saveCrop').textContent='将框选区域加入配图';}
function drawCrop(){if(!state.crop)return;const[x0,y0,x1,y1]=state.crop;Object.assign($('cropSelection').style,{left:x0*100+'%',top:y0*100+'%',width:(x1-x0)*100+'%',height:(y1-y0)*100+'%'});$('cropSelection').hidden=false;$('saveCrop').disabled=state.busy||x1-x0<.02||y1-y0<.02;}
let dragStart=null;
function coords(e){const r=$('cropStage').getBoundingClientRect();return[Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))];}
$('cropStage').addEventListener('pointerdown',e=>{dragStart=coords(e);$('cropStage').setPointerCapture(e.pointerId);});
$('cropStage').addEventListener('pointermove',e=>{if(!dragStart)return;const p=coords(e);state.crop=[Math.min(dragStart[0],p[0]),Math.min(dragStart[1],p[1]),Math.max(dragStart[0],p[0]),Math.max(dragStart[1],p[1])];drawCrop();});
$('cropStage').addEventListener('pointerup',()=>dragStart=null);

$('arxivForm').addEventListener('submit',guarded(async e=>{e.preventDefault();if(!approveNavigation())return;$('arxivSubmit').disabled=true;try{const r=await request('/api/import/arxiv',{url:$('arxivUrl').value,auto_draft:$('arxivAutoDraft').checked});await openJob(r.id);if(r.message)toast(r.message);}finally{$('arxivSubmit').disabled=false;}}));
$('arxivAutoDraft').onchange=()=>{$('arxivSubmit').textContent=$('arxivAutoDraft').checked?'生成并投递草稿 →':'解析论文 →';};
async function upload(file){if(!file)return;if(file.size>60*1024*1024)throw new Error('PDF 不能超过 60 MB。');const r=await request('/api/import/pdf',file,true);await openJob(r.id);$('pdfInput').value='';}
$('pdfInput').addEventListener('change',guarded(e=>upload(e.target.files[0])));
for(const name of ['dragenter','dragover'])$('dropZone').addEventListener(name,e=>{e.preventDefault();$('dropZone').classList.add('drag');});
$('dropZone').addEventListener('dragleave',()=>$('dropZone').classList.remove('drag'));
$('dropZone').addEventListener('drop',guarded(async e=>{e.preventDefault();$('dropZone').classList.remove('drag');await upload(e.dataTransfer.files[0]);}));
$('exampleLink').onclick=()=>$('arxivUrl').value='https://arxiv.org/abs/2212.10156';
$('newPaper').onclick=()=>{if(!approveNavigation())return;clearTimeout(state.timer);state.active=null;state.dirty=false;$('workspace').hidden=true;$('welcome').hidden=false;$('taskBanner').hidden=true;refreshHistory().catch(e=>toast(e.message,true));};
$('settingsButton').onclick=()=>$('settingsDialog').showModal();$('configureInline').onclick=()=>$('settingsDialog').showModal();
$('helpButton').onclick=()=>$('helpDialog').showModal();
document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>$(b.dataset.close).close());
$('settingsForm').onsubmit=guarded(async e=>{e.preventDefault();const remember=$('rememberModels').checked;if(state.desktop){await request('/api/credentials',{...settings(),api_key:$('apiKey').value,profile_id:state.profileId||'',name:$('profileName').value.trim(),remember});await refreshModels();} $('settingsDialog').close();$('modelBadge').textContent=$('modelId').value||'模型已设置';toast(remember&&state.desktop?'全部模型配置已在软件目录加密保存。':'模型配置仅保留在本次运行内存中。');});
$('newModel').onclick=newModel;
$('modelProfiles').onchange=guarded(async()=>{const id=$('modelProfiles').value;if(!id){newModel();return;}await request('/api/credentials',{activate:id});await refreshModels();toast('已切换写作模型。');});
$('deleteModel').onclick=guarded(async()=>{if(!state.profileId)return;if(!confirm('删除这个模型配置及其保存的密钥？'))return;await request('/api/credentials',{delete:state.profileId});await refreshModels();toast('配置已删除。');});
$('clearKey').onclick=guarded(async()=>{if(!confirm('清除全部模型配置与加密文件？之后需要重新填写。'))return;if(state.desktop){await request('/api/credentials',{clear:true});await refreshModels();} $('apiKey').value='';$('modelBadge').textContent='密钥已清除';toast('内存配置与加密文件已清除；正在执行的请求需取消或退出软件。');});
$('openData').onclick=guarded(()=>request('/api/desktop/action',{action:'open-data'}));
$('openPdf').addEventListener('click',guarded(async e=>{if(state.desktop){e.preventDefault();await request('/api/desktop/action',{action:'open-pdf',id:state.active});}}));
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>showTab(b.dataset.tab));
$('history').addEventListener('click',guarded(async e=>{const b=e.target.closest('[data-job]');if(b&&approveNavigation())await openJob(b.dataset.job);}));
$('generate').onclick=guarded(async()=>{if(!$('modelId').value){$('settingsDialog').showModal();return;}await savePaperInfo();await saveFigures(false);if(state.dirty)await saveDraft(false);await request(endpoint('generate'),options());await watchJob(state.active);});
$('saveDraft').onclick=guarded(()=>saveDraft());
$('draftEditor').addEventListener('input',()=>{state.dirty=true;$('saveDraft').textContent='保存修改';});
$('draftEditor').addEventListener('click',e=>{const b=e.target.closest('[data-title-option]');if(b){document.querySelector('[data-field=title]').value=state.article.title_options[Number(b.dataset.titleOption)];state.dirty=true;$('saveDraft').textContent='保存修改';}if(e.target.closest('[data-configure]'))$('settingsDialog').showModal();});
$('theme').onchange=renderPreview;
$('mobilePreview').onclick=()=>{$('preview').parentElement.classList.remove('wide');$('mobilePreview').classList.add('active');$('widePreview').classList.remove('active');};
$('widePreview').onclick=()=>{$('preview').parentElement.classList.add('wide');$('widePreview').classList.add('active');$('mobilePreview').classList.remove('active');};
$('paperInfoPanel').addEventListener('input',()=>{state.metadataDirty=true;$('savePaperInfo').textContent='保存论文资料';});
$('savePaperInfo').onclick=guarded(()=>savePaperInfo(true));
$('repairCrops').onclick=guarded(async()=>{await saveDraft(false);await saveFigures(false);await request(endpoint('repair-crops'),{});await watchJob(state.active);});
$('saveFigures').onclick=guarded(()=>saveFigures());$('pageSelect').onchange=()=>showPage();$('resetCrop').onclick=resetCrop;
$('figureGallery').addEventListener('click',e=>{const replace=e.target.closest('[data-replace-figure]');if(replace){$('materialsPanel').open=true;$('materialTarget').value=replace.dataset.replaceFigure;$('materialsPanel').scrollIntoView({behavior:'smooth'});return;}const pageButton=e.target.closest('[data-open-page]');if(pageButton){showPage(Number(pageButton.dataset.openPage));$('cropStage').scrollIntoView();return;}const b=e.target.closest('[data-view-figure]');if(!b)return;const f=state.source.figures.find(f=>f.id===b.dataset.viewFigure);showPage(f.page);const p=state.source.pages[f.page-1];state.crop=[f.bbox[0]/p.width,f.bbox[1]/p.height,f.bbox[2]/p.width,f.bbox[3]/p.height];state.editFigure=f.id;$('cropCaption').value=f.caption;$('saveCrop').textContent='更新这张配图';drawCrop();$('cropStage').scrollIntoView({behavior:'smooth',block:'center'});});
$('saveCrop').onclick=guarded(async()=>{await saveFigures(false);state.source=await request(endpoint('crop'),{page:Number($('pageSelect').value),box:state.crop,caption:$('cropCaption').value,figure_id:state.editFigure});renderFigures();resetCrop();renderPreview();toast('配图已保存，保留原页来源。');});
$('auditContent').addEventListener('click',e=>{const b=e.target.closest('[data-source-page]');if(b){showTab('figures');showPage(Number(b.dataset.sourcePage));}});
$('cancelTask').onclick=guarded(async()=>{await request(endpoint('cancel'),{});toast('已请求取消；当前模型请求结束后会停止。');});
$('exportPrompt').onclick=guarded(async()=>{await savePaperInfo();await saveFigures(false);if(state.desktop){await request('/api/desktop/action',{action:'prompt',id:state.active,options:options()});}else{const r=await request(endpoint('prompt'),options());downloadText(r.prompt,'paper-writing-prompt.txt');}toast('提示词包含全文、配图 ID、页码和成稿 JSON 格式。');});
$('importDraft').onclick=()=>$('jsonDialog').showModal();
$('confirmJson').onclick=guarded(async()=>{let article;try{article=JSON.parse($('articleJson').value.trim().replace(/^```(?:json)?\s*|\s*```$/g,''));}catch{throw new Error('JSON 格式错误，请粘贴完整对象。');}await request(endpoint('article'),article);state.article=await request(endpoint('article'));state.dirty=false;$('jsonDialog').close();renderEditor();renderPreview();await renderAudit();busy(false);toast('成稿已导入，请查看证据提醒。');});
async function exportFile(format){await saveFigures(false);await saveDraft(false);if(state.desktop){const r=await request('/api/desktop/action',{action:'export',id:state.active,format,theme:$('theme').value});if(!r.cancelled)toast('文件已保存：'+r.name);return;}const a=document.createElement('a');a.href=endpoint('export')+'?format='+format+'&theme='+$('theme').value;a.download='';a.click();}
$('exportZip').onclick=guarded(()=>exportFile('zip'));$('exportMd').onclick=guarded(()=>exportFile('md'));
$('copyHtml').onclick=guarded(async()=>{await saveFigures(false);await saveDraft(false);const r=await fetch(endpoint('export')+'?format=html&theme='+$('theme').value);if(!r.ok)throw new Error('导出失败');const html=await r.text();if(!navigator.clipboard?.write||!window.ClipboardItem){if(state.desktop)await exportFile('html');else downloadText(html,'wechat.html','text/html');toast('浏览器不支持富文本复制，已下载 HTML。');return;}try{await navigator.clipboard.write([new ClipboardItem({'text/html':new Blob([html],{type:'text/html'}),'text/plain':new Blob([state.article.sections.flatMap(s=>s.paragraphs.map(p=>p.text)).join('\n\n')],{type:'text/plain'})})]);toast('已复制正文。微信可能不保留剪贴板图片，请逐张上传并确认。');}catch{if(state.desktop)await exportFile('html');else downloadText(html,'wechat.html','text/html');toast('复制权限未开启，已下载 HTML。');}});
$('skillFormat').onclick=guarded(async()=>{if(state.reviewDirty)await saveReviewOptions();await saveFigures(false);await saveDraft(false);await request(endpoint('skill'),{});await watchJob(state.active);});
window.addEventListener('beforeunload',e=>{if(state.dirty||state.metadataDirty||state.figuresDirty||state.reviewDirty){e.preventDefault();e.returnValue='';}});
guarded(async()=>{await refreshModels();await refreshHistory();window.paperStudioReady=true;})();

window.paperStudioStatus=()=>({dirty:state.dirty||state.metadataDirty||state.figuresDirty||state.reviewDirty,busy:state.busy});


// Publication review is distinct from model generation and machine evidence checks.
let wechatConfig={},wechatWorking=false;
function resetHumanChecks(){document.querySelectorAll('[data-review-check]').forEach(e=>e.checked=false);}
function invalidateReviewLocally(){if(!state.active)return;if(state.wechatReview)state.wechatReview.approved=false;resetHumanChecks();updateReviewButtons();$('wechatReviewState').textContent='内容有修改，请保存并重新人工审核。';}
function markReviewDirty(){if(!state.active)return;state.reviewDirty=true;invalidateReviewLocally();}
function updateWechatCounts(){
  for(const [id,limit] of [['wechatTitle',32],['wechatDigest',120]]){
    const count=Array.from($(id).value.trim()).length;
    $(id+'Count').textContent=`${count} / ${limit} 个字符`+(count>limit?' · 超出时保存会自动整理':'');
    $(id+'Count').classList.toggle('field-over-limit',count>limit);
  }
}
function renderFieldAdjustments(changes=[]){
  state.wechatFieldAdjustments=changes;
  $('wechatFieldAdjustments').hidden=!changes.length;
  $('wechatFieldAdjustmentText').textContent=changes.map(c=>`${c.field==='title'?'标题':'摘要'}：${c.reason}\n原文（${Array.from(c.before).length} 字符）：${c.before}\n提交版（${Array.from(c.after).length} 字符）：${c.after}`).join('\n\n');
}
function updateReviewButtons(){
  const r=state.wechatReview||{},changed=state.reviewDirty||state.dirty||state.metadataDirty||state.figuresDirty;
  const active=state.busy||wechatWorking;
  $('fitWechatFields').disabled=active||!state.article;
  const terminal=['unknown','submitted','submitted_unverified'].includes(r.submission?.state);
  $('submitWechat').disabled=active||changed||!r.approved||!wechatConfig.configured||terminal;
  $('approveWechat').disabled=active||changed||!state.article||!wechatConfig.configured||Boolean(r.blocker);
  $('revokeWechat').disabled=active||!r.approved;
}
function renderWechatAccount(){
  $('wechatAccountLabel').textContent=wechatConfig.configured?'目标公众号：'+(wechatConfig.name||'未填写名称')+' · '+wechatConfig.appid:'尚未连接公众号，请先打开“公众号设置”。';
}
function allCovers(){return [...(state.source?.covers||[]).slice().reverse(),...(state.source?.figures||[])];}
function fillCovers(){const previous=$('wechatCover').value;$('wechatCover').innerHTML='<option value="">请选择封面</option>'+allCovers().map(f=>`<option value="${escapeHTML(f.id)}">${escapeHTML((f.kind==='designed_cover'?'设计封面':f.id)+' · '+(f.caption||'').slice(0,90))}</option>`).join('');$('wechatCover').value=previous;}
function updateCoverPreview(){const f=allCovers().find(x=>x.id===$('wechatCover').value);$('wechatCoverPreview').hidden=!f;if(f)$('wechatCoverPreview').src=asset(f.image);}
$('generateCover').onclick=guarded(async()=>{await saveDraft(false);const covers=await request(endpoint('cover'),{title:$('coverTitle').value.trim()||$('wechatTitle').value,label:$('coverLabel').value,theme:$('wechatTheme').value==='baoyu'?'ink':$('wechatTheme').value});state.source.covers=[...(state.source.covers||[]),...covers];fillCovers();$('wechatCover').value=covers[0].id;updateCoverPreview();markReviewDirty();toast('已生成横版和方形封面；当前选择横版，请保存提交设置。');});
async function refreshWechatReview(){
  if(!state.active)return;
  wechatConfig=await request('/api/wechat');renderWechatAccount();
  const r=await request(endpoint('wechat'));state.wechatReview=r;
  if(!state.reviewDirty){
    $('wechatTitle').value=r.options.title||'';$('wechatAuthor').value=r.options.author||'';$('wechatDigest').value=r.options.digest||'';
    $('wechatSource').value=r.options.source_url||state.source.publication_info?.paper_url||'';$('wechatTheme').value=r.options.theme||'ink';$('baoyuTheme').value=r.options.baoyu_theme||'simple';
    fillCovers();
    $('wechatCover').value=r.options.cover_id||'';updateCoverPreview();
    renderFieldAdjustments(r.field_adjustments||[]);
  }
  updateWechatCounts();
  $('wechatWarnings').textContent=[r.blocker,r.video_count?`含 ${r.video_count} 段视频来源卡。视频文件不会自动插入公众号，请提交后在微信后台补入。`:'',r.html_chars?`待上传 HTML：${r.html_chars.toLocaleString()} 字符。超过 1 MB 的图片将尝试转为 JPEG，保持原尺寸；预览使用实际待上传图片。`:''].filter(Boolean).join('\n');
  $('wechatReviewState').textContent=r.approved&&!state.reviewDirty&&!state.dirty&&!state.metadataDirty&&!state.figuresDirty?'人工审核已通过，可提交当前版本。':'当前版本尚未通过人工审核。';
  if(!r.blocker)$('wechatPreview').src=endpoint('wechat-preview')+'?v='+Date.now();else $('wechatPreview').removeAttribute('src');
  const sub=r.submission||{};$('wechatSubmission').hidden=!sub.message;
  $('wechatSubmission').textContent=(sub.message||'')+(sub.media_id?'\n草稿 ID：'+sub.media_id:'');
  $('recheckWechat').hidden=!sub.media_id;$('resetWechat').hidden=!['submitted','submitted_unverified','unknown'].includes(sub.state);
  updateReviewButtons();
}
async function saveReviewOptions(){
  if(state.figuresDirty)await saveFigures(false);
  if(state.dirty)await saveDraft(false);else await savePaperInfo();
  await request(endpoint('wechat-options'),{title:$('wechatTitle').value,author:$('wechatAuthor').value,digest:$('wechatDigest').value,cover_id:$('wechatCover').value,theme:$('wechatTheme').value,baoyu_theme:$('baoyuTheme').value,source_url:$('wechatSource').value,field_adjustments:state.wechatFieldAdjustments||[]});
  state.reviewDirty=false;resetHumanChecks();await refreshWechatReview();
}
async function saveWechatConfig(check=false){
  if(wechatWorking)return;wechatWorking=true;
  try{
    wechatConfig=await request('/api/wechat/config',{name:$('wechatName').value,appid:$('wechatAppId').value.trim(),secret:$('wechatSecret').value.trim(),remember:$('rememberWechat').checked});
    $('wechatSecret').value='';$('wechatSecret').placeholder='已配置；留空保留当前账号密钥';
    $('wechatConnectionState').textContent='配置已保存。';renderWechatAccount();
    if(check){$('wechatConnectionState').textContent='正在连接微信官方接口…';wechatConfig=await request('/api/wechat/check',{});$('wechatConnectionState').textContent=wechatConfig.check.message;}
    if(state.active)await refreshWechatReview();
  }catch(e){$('wechatConnectionState').textContent=e.message;throw e;}
  finally{wechatWorking=false;updateReviewButtons();}
}
$('wechatSettings').addEventListener('click',guarded(async()=>{
  wechatConfig=await request('/api/wechat');$('wechatName').value=wechatConfig.name;$('wechatAppId').value=wechatConfig.appid;$('wechatSecret').value='';$('rememberWechat').checked=wechatConfig.remember;
  $('wechatSecret').placeholder=wechatConfig.configured?'已配置；留空保留当前账号密钥':'仅在本机填写 AppSecret';$('wechatConnectionState').textContent=wechatConfig.warning||wechatConfig.check?.message||'';$('wechatDialog').showModal();
}));
$('wechatForm').addEventListener('submit',guarded(async e=>{e.preventDefault();await saveWechatConfig();}));
$('checkWechat').addEventListener('click',guarded(()=>saveWechatConfig(true)));
$('clearWechat').addEventListener('click',guarded(async()=>{if(!confirm('清除本机公众号配置与加密文件？不会删除公众号文章。'))return;wechatConfig=await request('/api/wechat/config',{clear:true});$('wechatSecret').value='';$('wechatAppId').value='';$('wechatName').value='';$('wechatConnectionState').textContent='公众号配置已清除。';if(state.active)await refreshWechatReview();}));
$('saveWechatOptions').addEventListener('click',guarded(async()=>{await saveReviewOptions();toast('已更新待提交稿，请通读并完成人工审核。');}));
$('fitWechatFields').addEventListener('click',guarded(async()=>{
  const fitted=await request(endpoint('wechat-fit'),{title:$('wechatTitle').value,digest:$('wechatDigest').value});
  $('wechatTitle').value=fitted.options.title;$('wechatDigest').value=fitted.options.digest;
  const merged=new Map((state.wechatFieldAdjustments||[]).map(c=>[c.field,c]));
  fitted.field_adjustments.forEach(c=>merged.set(c.field,c));
  renderFieldAdjustments([...merged.values()]);updateWechatCounts();markReviewDirty();
  toast(fitted.field_adjustments.length?'已整理提交字段，原稿不变；请检查并保存。':'标题与摘要已符合长度要求。');
}));
$('approveWechat').addEventListener('click',guarded(async()=>{
  const checks={};document.querySelectorAll('[data-review-check]').forEach(e=>checks[e.dataset.reviewCheck]=e.checked);
  await request(endpoint('wechat-approve'),{checks,reviewer:$('wechatReviewer').value});await refreshWechatReview();toast('当前版本已通过人工审核。');
}));
$('revokeWechat').addEventListener('click',guarded(async()=>{await request(endpoint('wechat-revoke'),{});resetHumanChecks();await refreshWechatReview();}));
$('submitWechat').addEventListener('click',guarded(async()=>{
  if(state.reviewDirty||state.dirty||state.metadataDirty||state.figuresDirty)throw new Error('有未保存修改，请先保存并重新审核。');
  if(wechatWorking)return;wechatWorking=true;updateReviewButtons();
  try{await request(endpoint('wechat-submit'),{});busy(true);await watchJob(state.active);}finally{wechatWorking=false;updateReviewButtons();}
}));
$('recheckWechat').addEventListener('click',guarded(async()=>{await request(endpoint('wechat-recheck'),{});busy(true);await watchJob(state.active);}));
$('resetWechat').addEventListener('click',guarded(async()=>{if(!confirm('请先检查公众号草稿箱。继续将允许创建另一份草稿，已有草稿不会删除。确定已检查并需要重新提交？'))return;await request(endpoint('wechat-reset'),{confirmed:true});await refreshWechatReview();}));
for(const id of ['wechatTitle','wechatAuthor','wechatDigest','wechatCover','wechatTheme','wechatSource','baoyuTheme'])$(id).addEventListener('input',()=>{markReviewDirty();updateWechatCounts();if(id==='wechatCover')updateCoverPreview();});
for(const id of ['draftEditor','paperInfoPanel'])$(id)?.addEventListener('input',invalidateReviewLocally);
for(const id of ['figureGallery','projectVideos'])$(id)?.addEventListener('input',()=>{state.figuresDirty=true;invalidateReviewLocally();});

$('reviewBaoyu').onclick=guarded(async()=>{await saveReviewOptions();await request(endpoint('skill'),{});await watchJob(state.active);});

async function renderMaterials(){
  const id=state.active;const c=await request(endpoint('materials'));if(id!==state.active)return;
  $('materialsNotes').textContent=(c.notes||[]).join(' ');
  $('materialGallery').innerHTML=(c.items||[]).map(i=>`<article class="material-card"><a href="${asset(i.image)}" target="_blank" rel="noopener"><img src="${asset(i.image)}" loading="lazy" alt="${escapeHTML(i.caption)}"></a><p>${i.width} × ${i.height} px · p. ${i.pages.join(', ')}</p><div class="button-row"><button class="secondary" data-accept-material="${i.id}">使用此素材</button><button class="text-button" data-material-page="${i.pages[0]}">对照原页</button></div></article>`).join('');
}
async function prepareMaterialChange(){if(state.busy)throw new Error('请等待当前任务完成。');await saveDraft(false);await saveFigures(false);}
async function materialChanged(source){state.source=source;renderFigures();renderPreview();invalidateReviewLocally();await renderAudit();toast('图片已保存。请核对完整性；替换图片后需重新审核。');}
$('scanMaterials').onclick=guarded(async()=>{await prepareMaterialChange();await request(endpoint('scan-materials'),{});await watchJob(state.active);});
$('imageInput').onchange=guarded(async()=>{const file=$('imageInput').files[0];if(!file)return;try{if(file.size>20*1024*1024)throw new Error('图片不能超过 20 MB。');await prepareMaterialChange();const q=new URLSearchParams({filename:file.name,caption:$('materialCaption').value,page:$('materialPage').value,replace_id:$('materialTarget').value});await materialChanged(await request(endpoint('import-image')+'?'+q,file,true));}finally{$('imageInput').value='';}});
$('materialGallery').onclick=guarded(async e=>{const page=e.target.closest('[data-material-page]');if(page){showPage(Number(page.dataset.materialPage));$('cropStage').scrollIntoView();return;}const b=e.target.closest('[data-accept-material]');if(!b)return;await prepareMaterialChange();await materialChanged(await request(endpoint('accept-material'),{id:b.dataset.acceptMaterial,replace_id:$('materialTarget').value||null,caption:$('materialCaption').value}));});

let feedTimer;
async function refreshFeed(fill=false){
  const f=await request('/api/autofeed');state.feed=f;
  $('feedBadge').textContent=f.running?'运行中':f.config.enabled?'已启用':'已暂停';
  $('feedStatus').textContent=`已入列 ${f.candidate_count??f.items.length} 篇标题 · ${f.message}`;
  if(fill){
    const session=await request('/api/session'),account=await request('/api/wechat');
    $('feedModel').innerHTML=(session.profiles||[]).map(p=>`<option value="${escapeHTML(p.id)}">${escapeHTML(p.name||p.model)}</option>`).join('');
    $('feedModel').value=f.config.model_profile||session.active_profile||'';
    $('feedMax').value=f.config.max_daily;$('feedStyle').value=f.config.style;
    $('feedVision').checked=f.config.vision;$('feedEnabled').checked=f.config.enabled;
    $('feedTopics').innerHTML=f.topics.map(t=>`<label class="checkbox"><input type="checkbox" data-feed-topic="${t.id}" ${f.config.topics.includes(t.id)?'checked':''}>${escapeHTML(t.label)}</label>`).join('');
    $('feedBinding').textContent='目标公众号：'+(account.name||account.appid||'尚未配置')+'。自动配置绑定此账号与所选模型；切换账号后须重新保存。';
  }
  $('feedSave').disabled=f.running;$('feedRun').disabled=f.running||!f.config.enabled;$('feedDiscover').disabled=f.running;
  renderFeedQueue();
  const q=f.selected_queue||{};
  $('feedFinish').disabled=!f.running||f.mode==='discovery';$('feedPause').disabled=!f.running&& !f.config.enabled;
  $('feedResume').disabled=f.running||!q.urls?.length||q.next>=q.urls.length;
  $('feedSerial').textContent=(q.urls?.length?`所选队列：已完成 ${q.next}/${q.urls.length} 篇 · ${f.running?'处理中':q.state==='complete'?'已完成':'已停止，可继续'}。未开始的论文不会下载 PDF。`:'每次选 1–5 篇，使用当前模型与公众号。停止会在当前网络请求结束后生效，后续 PDF 不会提前下载。')+' 新稿自适应写作与排版，模型读取文本，原图用于配图；编辑作品前请先停止队列。';
  clearTimeout(feedTimer);
  if($('feedDialog').open)feedTimer=setTimeout(()=>guarded(()=>refreshFeed())(),2000);
}
function visibleFeedItems(){const q=$('feedSearch').value.trim().toLowerCase();return(state.feed?.items||[]).filter(i=>!q||((i.title||'')+' '+i.id).toLowerCase().includes(q));}
function renderFeedQueue(){
  const f=state.feed;if(!f)return;const items=visibleFeedItems();
  const labels={candidate:'标题已取得',resources_pending:'项目/代码待核实',processing:'正在生成',held:'待处理',submitted:'已投递草稿',submitted_unverified:'待核对提交',unknown:'提交结果待核对',existing:'已在作品库'};
  $('feedCount').textContent=`当前显示 ${items.length} 篇 · 已选 ${state.feedSelected.size} 篇`;
  $('feedSelected').disabled=f.running||!state.feedSelected.size;
  $('feedQueue').innerHTML=items.length?items.map(i=>`<article class="feed-card"><label class="feed-pick"><input type="checkbox" data-feed-pick="${escapeHTML(i.url)}" ${state.feedSelected.has(i.url)?'checked':''} ${f.running?'disabled':''}><span><a href="${escapeHTML(i.url)}" target="_blank" rel="noopener">${escapeHTML(i.title)}</a><small>${escapeHTML(i.url)} · ${escapeHTML((i.published||'').slice(0,10))} · ${escapeHTML(labels[i.state]||i.state)}</small></span></label><div class="button-row"><button class="secondary" data-feed-direct="${escapeHTML(i.url)}" ${f.running?'disabled':''}>一键生成并投递</button>${i.job_id?`<button class="text-button" data-feed-job="${i.job_id}">打开本地稿件</button>`:''}</div></article>`).join(''):'<p class="muted">暂无匹配标题；点击“获取最新标题与链接”开始。</p>';
}
$('feedSearch').oninput=renderFeedQueue;
$('feedCopy').onclick=guarded(async()=>{await navigator.clipboard.writeText(visibleFeedItems().map(i=>`${i.title}\n${i.url}`).join('\n\n'));toast('已复制当前列表的标题与 arXiv 链接。');});
$('feedQueue').onchange=e=>{const el=e.target.closest('[data-feed-pick]');if(!el)return;if(el.checked&&state.feedSelected.size>=5){el.checked=false;toast('每次最多选择 5 篇。',true);return;}if(el.checked)state.feedSelected.add(el.dataset.feedPick);else state.feedSelected.delete(el.dataset.feedPick);renderFeedQueue();};
async function startSelected(urls){if(!approveNavigation())return;const r=await request('/api/autofeed/links',{urls});state.feedSelected.clear();await refreshFeed();if(urls.length===1){$('feedDialog').close();await openJob(r.id);}if(r.message)toast(r.message);}
$('feedSelected').onclick=guarded(()=>startSelected([...state.feedSelected]));
$('feedFinish').onclick=guarded(async()=>{await request('/api/autofeed/finish-current',{});await refreshFeed();});
$('feedResume').onclick=guarded(async()=>{if(!approveNavigation())return;await request('/api/autofeed/resume',{});await refreshFeed();});
$('openAutoFeed').onclick=guarded(async()=>{await refreshFeed(true);$('feedDialog').showModal();await refreshFeed();});
$('feedDialog').addEventListener('close',()=>clearTimeout(feedTimer));
$('feedForm').onsubmit=guarded(async e=>{e.preventDefault();await request('/api/autofeed/config',{enabled:$('feedEnabled').checked,max_daily:Number($('feedMax').value),style:$('feedStyle').value,vision:$('feedVision').checked,model_profile:$('feedModel').value,topics:[...document.querySelectorAll('[data-feed-topic]:checked')].map(e=>e.dataset.feedTopic)});await refreshFeed(true);toast('自动配置已保存。');});
$('feedDiscover').onclick=guarded(async()=>{await request('/api/autofeed/discover',{});await refreshFeed();});
$('feedRun').onclick=guarded(async()=>{await request('/api/autofeed/run',{});await refreshFeed();});
$('feedPause').onclick=guarded(async()=>{await request('/api/autofeed/pause',{});await refreshFeed(true);});
$('feedQueue').onclick=guarded(async e=>{const direct=e.target.closest('[data-feed-direct]');if(direct){await startSelected([direct.dataset.feedDirect]);return;}const b=e.target.closest('[data-feed-job]');if(!b||!approveNavigation())return;$('feedDialog').close();await openJob(b.dataset.feedJob);});
