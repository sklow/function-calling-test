namespace FunctionCallingServer.Models;

/// <summary>
/// ツールのメタデータを表すレコード
/// </summary>
/// <param name="Name">ツール名</param>
/// <param name="Description">ツールの説明</param>
/// <param name="HttpMethod">HTTP メソッド（例: "POST"）</param>
/// <param name="Path">エンドポイントパス</param>
/// <param name="InputSchema">入力の JSON Schema</param>
/// <param name="OutputSchema">出力の JSON Schema</param>
/// <param name="RequiresAuth">認証が必要かどうか</param>
public record ToolMetadata(
    string Name,
    string Description,
    string HttpMethod,
    string Path,
    object InputSchema,
    object OutputSchema,
    bool RequiresAuth
);
