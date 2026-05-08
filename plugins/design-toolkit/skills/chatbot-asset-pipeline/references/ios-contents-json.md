# iOS asset catalog `Contents.json` shape

Drop this in `Assets.xcassets/<asset-name>.imageset/Contents.json`. Substitute the asset name in the three filenames.

```json
{
  "images" : [
    {
      "filename" : "<asset-name>@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "<asset-name>@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "<asset-name>@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "preserves-vector-representation" : false,
    "template-rendering-intent" : "original"
  }
}
```

Notes:

- `idiom: universal` is correct for illustrations that aren't device-specific. Use `iphone` / `ipad` only if the user explicitly wants different art per device.
- `template-rendering-intent: original` preserves color. Use `template` only for monochrome glyph-style illustrations the user wants tinted at runtime.
- `preserves-vector-representation` stays `false` — these are raster outputs from the chat UI, not PDFs.
