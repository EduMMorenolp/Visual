const COMFY = '/comfy'
const WORKFLOW_URLS = {
  sdxl: '/workflows/workflow_sdxl.json',
  flux: '/workflows/workflow_flux_nf4.json',
}

const $ = id => document.getElementById(id)
const form = $('generate-form')
const generateBtn = $('generate-btn')
const progressBar = $('progress-bar')
const resultImage = $('result-image')
const placeholder = $('placeholder')
const resultActions = $('result-actions')
const downloadBtn = $('download-btn')
const copyPromptBtn = $('copy-prompt-btn')
const errorMsg = $('error-msg')
const statusDot = $('status-dot')
const statusText = $('status-text')
const promptInput = $('prompt')
const modelSelect = $('model')

let currentImageUrl = null
let lastPrompt = ''

async function checkHealth() {
  try {
    const r = await fetch(`${COMFY}/`)
    if (r.ok) {
      statusDot.className = 'dot'
      statusText.textContent = 'ComfyUI conectado'
    } else {
      throw new Error('Not OK')
    }
  } catch {
    statusDot.className = 'dot error'
    statusText.textContent = 'ComfyUI no disponible'
  }
}

checkHealth()
setInterval(checkHealth, 15000)

function injectWorkflowParams(workflow, params) {
  for (const nodeId in workflow) {
    const node = workflow[nodeId]
    const nodeTitle = (node._meta?.title || '').toLowerCase()

    if (node.class_type === 'CLIPTextEncode' && node.inputs.text !== undefined) {
      if (nodeTitle.includes('negative')) continue
      node.inputs.text = params.prompt
    }

    if (node.class_type === 'EmptyLatentImage') {
      node.inputs.width = params.width
      node.inputs.height = params.height
    }

    if (node.class_type === 'KSampler') {
      if (params.steps != null) node.inputs.steps = params.steps
      if (params.seed >= 0) node.inputs.seed = params.seed
      node.inputs.cfg = params.model === 'flux' ? 1 : params.cfg
    }
  }

  let negativeSet = false
  for (const nodeId in workflow) {
    const node = workflow[nodeId]
    if (node.class_type === 'CLIPTextEncode' && node.inputs.text !== undefined) {
      const nodeTitle = (node._meta?.title || '').toLowerCase()
      if (nodeTitle.startsWith('negative') || node.inputs.text === '') {
        if (!negativeSet) {
          node.inputs.text = params.negativePrompt
          negativeSet = true
        }
      }
    }
  }
}

async function generateImage(params) {
  const r = await fetch(WORKFLOW_URLS[params.model])
  if (!r.ok) throw new Error(`No se pudo cargar el workflow (${r.status})`)
  const workflow = await r.json()

  injectWorkflowParams(workflow, params)

  const queueR = await fetch(`${COMFY}/prompt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt: workflow, client_id: crypto.randomUUID() }),
  })

  if (!queueR.ok) {
    const err = await queueR.json().catch(() => ({}))
    throw new Error(err.error || `Error ${queueR.status} de ComfyUI`)
  }

  const { prompt_id } = await queueR.json()
  if (!prompt_id) throw new Error('ComfyUI no devolvió un prompt_id')

  for (let i = 0; i < 300; i++) {
    await new Promise(r => setTimeout(r, 500))
    try {
      const histR = await fetch(`${COMFY}/history/${prompt_id}`)
      if (!histR.ok) continue
      const data = await histR.json()
      if (data[prompt_id]?.outputs) {
        const outputs = data[prompt_id].outputs
        for (const nodeId in outputs) {
          const images = outputs[nodeId]?.images
          if (images?.length > 0) {
            const img = images[0]
            const params = new URLSearchParams({
              filename: img.filename,
              subfolder: img.subfolder || '',
              type: img.type || 'output',
            })
            return `${COMFY}/view?${params}`
          }
        }
      }
    } catch {
      // continue polling
    }
  }

  throw new Error('Timeout esperando la generación')
}

form.addEventListener('submit', async (e) => {
  e.preventDefault()
  errorMsg.style.display = 'none'

  const prompt = promptInput.value.trim()
  if (!prompt) {
    showError('El prompt no puede estar vacío')
    return
  }

  lastPrompt = prompt

  generateBtn.classList.add('loading')
  generateBtn.disabled = true
  progressBar.classList.add('active')
  resultImage.style.display = 'none'
  placeholder.style.display = 'block'
  placeholder.querySelector('p').textContent = 'Generando imagen...'
  resultActions.style.display = 'none'

  const params = {
    prompt,
    negativePrompt: $('negative-prompt').value,
    model: modelSelect.value,
    seed: parseInt($('seed').value),
    steps: parseInt($('steps').value),
    cfg: parseFloat($('cfg').value),
    width: parseInt($('width').value),
    height: parseInt($('height').value),
  }

  try {
    const url = await generateImage(params)

    if (currentImageUrl) URL.revokeObjectURL(currentImageUrl)

    const imgR = await fetch(url)
    if (!imgR.ok) throw new Error('Error al descargar la imagen')

    const blob = await imgR.blob()
    currentImageUrl = URL.createObjectURL(blob)

    placeholder.style.display = 'none'
    resultImage.src = currentImageUrl
    resultImage.style.display = 'block'
    resultActions.style.display = 'flex'
  } catch (err) {
    showError(err.message)
    placeholder.querySelector('p').textContent = 'Completa el prompt y haz clic en "Generar imagen"'
  } finally {
    generateBtn.classList.remove('loading')
    generateBtn.disabled = false
    progressBar.classList.remove('active')
  }
})

downloadBtn.addEventListener('click', () => {
  if (!currentImageUrl) return
  const a = document.createElement('a')
  a.href = currentImageUrl
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  a.download = `comfyui_${timestamp}.png`
  a.click()
})

copyPromptBtn.addEventListener('click', () => {
  navigator.clipboard.writeText(lastPrompt).then(() => {
    copyPromptBtn.textContent = 'Copiado!'
    setTimeout(() => { copyPromptBtn.textContent = 'Copiar prompt' }, 2000)
  })
})

modelSelect.addEventListener('change', (e) => {
  const isFlux = e.target.value === 'flux'
  $('cfg').value = isFlux ? '1' : '7'
  $('steps').value = isFlux ? '28' : '30'
})

function showError(msg) {
  errorMsg.textContent = msg
  errorMsg.style.display = 'block'
}
