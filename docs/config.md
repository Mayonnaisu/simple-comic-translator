## CONFIG OPTIONS

### GENERAL
```jsonc
"gpu_mode": false,              // use GPU mode
"debug_mode": false,            // use DEBUG mode
"result": {
  "overwrite": false,           // overwrite existing output images
  "load_json": false,           // load existing result.json
  "json_path": "output"         // path to result.json: "input"/"output"
}
```

> [!IMPORTANT]
> I'm not done with GPU mode yet, so it won't work. It can work if you know what you're doing tho.

> [!TIP]
> You can use either **config.json** or arguments to enable the settings above. If any of the settings is set to `true` in either of the methods, it will be enabled. However, to disable the setting, you need to disable it in both of the methods.

### IMAGE_MERGE
```jsonc
"enable": true                  // enable or disable merging, including IMAGE_SPLIT
```

> [!TIP]
> You can disable image merging if your comics don't have splitted text areas (paged format). Well, even if it is left enabled when there's no splitted text areas, it can still work fine. It's just that the output images will be splitted differently from the original images.

### DETECTION
```jsonc
"confidence_threshold": 0.3,     // minimum detection score: 0-1
"merge_threshold": 0.2,          // minimum IoU (overlap) to merge overlapping boxes: 0-1
"merge_times": 2,                // number of times to merge overlapping boxes
"tile": {
  "width": "original",           // width of each tile: "original" (image width)/number
  "height": "tile_width",        // height of each tile: "tile_width"/number
  "overlap": 0.5                 // overlap of each tile
}
```

> [!TIP]
> - Increase `merge_threshold` value if there are overlapping boxes that shouldn't be merged, and vice versa.
>
> - Increase `merge_times` value if somehow calling boxes-merging function 2x still leaves some overlapping boxes unmerged. I had to add this option because 1x isn't enough to merge all overlapping boxes in my testings.
>
> - It's recommended to set `tile_width` to `640` if you want to use number instead of `"original"` because the detection model works accurately when the image sizes are 640x640 px.
>
>   However, if you choose to use `"original"`, it will be faster when the original image width is bigger than 640. It's because in that case there will be fewer tiles to process. The thing is there's automatic resizing under the hood in case the image sizes aren't equal to 640x640 px to make sure it fits into the model.
>
>   Still, it may be less accurate than directly processing the real, unresized 640x640 tiles. 

### OCR
```jsonc
"source_language": "korean",    // input language: "jp", "korean", "ch", "en", etc
"confidence_threshold": 0.5,    // minimum recognition score: 0-1
"upscale": {
  "enable": false,              // enable or disable upscaling
  "ratio": 2                    // upscaling ratio: number
}
```

> [!TIP]
> - For Japanese language, you can use `"japanese"`, `"japan"`, `"jpn"`, `"jp"`, or `"ja"`. And it will automatically use Manga OCR instead PaddleOCR engine.
>
> - For other language codes, see https://github.com/Mushroomcat9998/PaddleOCR/blob/main/doc/doc_en/multi_languages_en.md#5-support-languages-and-abbreviations. Idk which ones are and aren't supported by PP-OCRv5 model tho.
>
> - As for upscaling, it can actually be used for downscaling as well (not recommended since less accurate). Use number >= 1 for upscaling and number < 1 for downscaling. The number can be integer/float.

### IMAGE_SPLIT
```jsonc
"max_height": 2000              // maximum height of each safe split
```

### TRANSLATION
```jsonc
"target_language": "en",        // translation language
"max_retries": 3,               // maximum retry attempts
"retry_delay": 30,              // retry delay in seconds
"timeout": 300,                 // timeout in seconds
"translator": {
  "provider": "gemini",         // provider: "gemini", "openai", "operouter", "ollama", etc
  "model": "gemini-2.5-flash",  // model ID
  "base_url": null,             // base url: "url"/null
  "temperature": 0.5,           // temperature
  "top_p": 0.8,                 // top p
  "max_output_tokens": 999999999  // max response tokens: number/null
},
"memory": {
  "enable": false,              // Use memory to translate
  "overwrite": false,           // overwite existing texts in memory
  "path": "output"              // path to memory file (.db/.db3/.sqlite/.sqlite3): "input"/"output"/path
},
"glossary_path": "output"       // path to glossary file (.json)
```

>[!NOTE]
> Base url is only required by some of providers that are self-hosted, custom, or Open-AI compatible endpoints. For example, `"http://localhost:11434"` for `"ollama"`.

> [!TIP]
> - You can use ISO language codes for brevity when setting `target_language`. For more ISO language codes, see https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes#Table.
>
> - When changing retry-related configs, you need to take into account the RPM (request per minute) limit for the selected model. 
>
> - To see Gemini model IDs, visit https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions#gemini-auto-updated.
>
> - To see the other providers, check out [LiteLLM Supported Providers](https://github.com/BerriAI/litellm?tab=readme-ov-file#supported-providers-website-supported-models--docs).
>
> - For `max_ouput_tokens`, 999999999 may not work for the other providers. In that case, you need to make sure it doesn't exceed the limit set by the provider, or just set it to `null`.

### OVERLAY
```jsonc
"box": {
  "offset": 10,                 // offset to enlarge text areas
  "padding": 10,                // padding to prevent text overflow
  "fill_color": "white",        // main color of text areas
  "outline_color": null,        // border color of text areas
  "outline_thickness": 1,       // border thickness of text areas
  "inpaint": false              // enable or disable inpainting (too slow, needs optimization)
},
"font": {
  "min_size": 11,               // minimum size of font
  "max_size": 40,               // maximum size of font
  "color": "black",             // font color
  "path": "fonts/NotoSerifKR-Bold.ttf" // path to font file
}
```

> [!TIP]
> - The color values can be color name (e.g. "red"), RGB tuple (e.g. (255,0,0) or (100%,0%,0%)), or hexadecimal strings (e.g. "#ff0000").
>
> - Fyi, that font file is used by default because it supports the Latin, Japanese, Korean, & Chinese characters among others. The support for other characters will always be useful because in debug mode the app will also save separate annotated images with the original texts.