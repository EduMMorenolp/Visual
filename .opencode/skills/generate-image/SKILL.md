---
name: generate-image
description: Generación de imágenes con ComfyUI + SDXL/FLUX. Mejora automática de prompts con técnicas avanzadas de prompt engineering, iluminación cinemática, términos de cámara y calidad.
license: MIT
compatibility: opencode
---

## Generación de imágenes con ComfyUI

Este skill contiene toda la base de conocimiento para generar imágenes de alta calidad usando ComfyUI con modelos SDXL y FLUX.

### Flujo de trabajo

1. El usuario da un prompt simple
2. Se mejora el prompt con términos de calidad, iluminación, cámara, estilo y composición
3. Se muestra el prompt mejorado al usuario
4. Se pregunta si quiere ajustar parámetros (seed, steps, cfg, resolución, modelo)
5. Se ejecuta la generación con `docker exec visual-comfyui-1 python3 /app/scripts/generate.py --prompt "..."`
6. Se muestra la imagen generada

---

### Estructura de prompt para SDXL

SDXL funciona mejor con **lenguaje natural descriptivo**, no con lists de tags como SD 1.5.

Template óptimo:
```
[Subject], [Scene/Context], [Lighting], [Camera/Lens], [Style], [Quality details]
```

Ejemplo completo:
```
Cinematic portrait of a Scandinavian woman with freckles, soft studio lighting, 85mm lens photography, film look, ultra detailed skin texture, sharp depth of field, magazine editorial style
```

---

### Categorías para mejorar prompts

#### 1. Términos de calidad
| Término | Efecto |
|---------|--------|
| `highly detailed` | Añade detalle general |
| `8k` / `ultra HD` | Sugiere alta resolución |
| `sharp focus` | Enfoque nítido |
| `intricate details` | Detalles intrincados |
| `masterpiece` | Calidad de obra maestra |
| `professional` | Aspecto profesional |

#### 2. Iluminación cinemática
| Término | Efecto |
|---------|--------|
| `cinematic lighting` | Iluminación de película |
| `volumetric lighting` | Rayos de luz visibles (god rays) |
| `golden hour` | Luz cálida de atardecer/amanecer |
| `dramatic shadows` | Sombras dramáticas |
| `rim light` | Luz de borde que separa sujeto del fondo |
| `studio lighting` | Iluminación controlada de estudio |
| `soft diffused light` | Luz suave y difusa |
| `Rembrandt lighting` | Triángulo de luz en la mejilla |
| `three-point lighting` | Key + fill + back light |
| `neon lighting` | Luces de neón (cyberpunk) |

#### 3. Cámara y lentes
| Término | Efecto |
|---------|--------|
| `shot on Canon EOS R5` | Especifica cámara real |
| `85mm lens` | Lente de retrato clásico |
| `50mm f/1.8` | Lente estándar gran apertura |
| `shallow depth of field` | Fondo borroso, sujeto enfocado |
| `bokeh` | Desenfoque artístico del fondo |
| `wide angle` | Gran angular para paisajes |
| `anamorphic lens` | Lente anamórfico (cinema) |
| `Arri Alexa` | Cámara de cine profesional |

#### 4. Composición
| Término | Efecto |
|---------|--------|
| `close-up` | Primer plano |
| `wide shot` | Plano general |
| `over-the-shoulder` | Sobre el hombro |
| `bird's-eye view` | Vista aérea |
| `low angle` | Contrapicado |
| `dynamic pose` | Pose dinámica |
| `epic composition` | Composición épica |

#### 5. Estilo artístico
| Término | Efecto |
|---------|--------|
| `cinematic` | Aspecto de película |
| `photorealistic` | Fotorrealista |
| `concept art` | Arte conceptual |
| `trending on ArtStation` | Estilo ArtStation |
| `magazine editorial` | Estilo editorial revista |
| `film grain` | Grano de película |
| `cinematic color grading` | Color grading cinematográfico |

---

### Técnicas por tipo de escena

#### Retrato
```
Cinematic portrait of [subject], [lighting], [camera/lens], shallow depth of field, bokeh background, ultra detailed skin texture, [style]
```

#### Paisaje
```
Epic landscape of [scene], [lighting], wide angle lens, deep focus, highly detailed, atmospheric perspective, [style]
```

#### Escena conceptual / fantasia
```
Concept art of [subject], dramatic lighting, volumetric light rays, epic composition, intricate details, trending on ArtStation, matte painting
```

#### Cyberpunk / Neon
```
[Subject] in cyberpunk city, neon pink and cyan lighting, reflective wet ground, night atmosphere, Blade Runner aesthetic, volumetric neon glow, cinematic grade
```

---

### Prompt weighting (énfasis)

Usar `(palabra:peso)` para aumentar o disminuir la importancia:

- `(keyword:1.2)` — aumenta énfasis 20%
- `(keyword:0.8)` — reduce énfasis 20%
- `((keyword))` — equivalente a 1.1x por paréntesis

No usar pesos >1.5 para evitar artefactos.

---

### Negative prompt por defecto

Siempre incluir en la generación:
```
low quality, blurry, pixelated, distorted, extra limbs, watermark, text, deformed hands, bad anatomy, lowres, ugly, cropped, worst quality
```

---

### Técnicas para FLUX

FLUX usa un enfoque diferente:
- **Prompts narrativos**: frases completas y naturales, no tags
- **Evitar exceso de tags**: FLUX prefiere descripciones fluidas
- **Estilo más libre**: no necesita tanto detalle técnico de cámara
- **CFG scale 1** (fijo en el workflow)

Ejemplo FLUX:
```
A majestic dragon soaring through storm clouds at sunset, lightning illuminating its scales, cinematic atmosphere, highly detailed
```

---

### Resolución nativa SDXL

Siempre usar resoluciones nativas SDXL para mejor calidad:
- Cuadrado: 1024×1024
- Retrato: 896×1152 / 832×1216
- Paisaje: 1152×896 / 1216×832
- Ultra-wide: 1536×640

---

### Parámetros recomendados

| Parámetro | SDXL | FLUX |
|-----------|------|------|
| Steps | 30 | 28 |
| CFG Scale | 7.0 | 1.0 |
| Sampler | euler | euler |
| Resolución | 1024×1024 | 1024×1024 |

---

### Flujo de mejora de prompt (paso a paso)

Dado un prompt simple del usuario, aplicar estas transformaciones en orden:

1. **Sujeto**: Describir con más detalle (edad, expresión, vestimenta, pose)
2. **Escena**: Añadir contexto ambiental (dónde, cuándo, atmósfera)
3. **Iluminación**: Elegir tipo de iluminación que mejor se adapte
4. **Cámara**: Añadir términos de fotografía si aplica
5. **Estilo**: Definir el estilo visual
6. **Calidad**: Añadir 2-3 términos de calidad
7. **Composición**: Especificar encuadre si relevante

No exceder ~100 palabras. SDXL funciona mejor con prompts concisos pero descriptivos.
