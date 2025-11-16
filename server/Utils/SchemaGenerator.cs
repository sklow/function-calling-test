using NJsonSchema;
using System.Text.Json;

namespace FunctionCallingServer.Utils;

/// <summary>
/// DTO クラスから JSON Schema を自動生成するユーティリティクラス
/// </summary>
public static class SchemaGenerator
{
    /// <summary>
    /// 指定した型 T から JSON Schema を生成する
    /// </summary>
    /// <typeparam name="T">スキーマ生成対象の型（クラス型）</typeparam>
    /// <returns>生成された JSON Schema オブジェクト</returns>
    public static object GenerateSchema<T>() where T : class
    {
        try
        {
            // 型 T から JSON Schema を生成
            var schema = JsonSchema.FromType<T>();

            // スキーマを匿名オブジェクトに変換して返す
            return ConvertSchemaToAnonymousObject(schema);
        }
        catch (Exception ex)
        {
            // エラーが発生した場合はログに記録し、空のスキーマを返す
            Console.Error.WriteLine($"JSON Schema 生成中にエラーが発生しました: {ex.Message}");
            return new { type = "object" };
        }
    }

    /// <summary>
    /// JsonSchema オブジェクトを匿名オブジェクトに変換する
    /// </summary>
    /// <param name="schema">変換対象の JsonSchema</param>
    /// <returns>匿名オブジェクトとして表現されたスキーマ</returns>
    private static object ConvertSchemaToAnonymousObject(JsonSchema schema)
    {
        // JSON 文字列に変換してから動的オブジェクトとしてデシリアライズ
        var json = schema.ToJson();
        var anonymousObject = JsonSerializer.Deserialize<object>(json);
        return anonymousObject ?? new { type = "object" };
    }
}
