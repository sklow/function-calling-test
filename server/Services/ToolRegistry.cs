using FunctionCallingServer.Models;
using FunctionCallingServer.Models.DTOs;
using FunctionCallingServer.Utils;

namespace FunctionCallingServer.Services;

/// <summary>
/// ツールレジストリのインターフェース
/// </summary>
public interface IToolRegistry
{
    /// <summary>
    /// すべてのツールのメタデータを取得
    /// </summary>
    IEnumerable<ToolMetadata> GetAllTools();
}

/// <summary>
/// ツールレジストリの実装
/// </summary>
public class ToolRegistry : IToolRegistry
{
    private readonly List<ToolMetadata> _tools = new();

    public ToolRegistry()
    {
        // ダミーデータ: 将来実装予定の get_weather ツール
        // SchemaGenerator を使用して DTO から JSON Schema を自動生成
        _tools.Add(new ToolMetadata(
            Name: "get_weather",
            Description: "指定した都市の現在の天気情報を取得します",
            HttpMethod: "POST",
            Path: "/tools/get_weather",
            InputSchema: SchemaGenerator.GenerateSchema<WeatherRequest>(),
            OutputSchema: SchemaGenerator.GenerateSchema<WeatherResponse>(),
            RequiresAuth: false
        ));
    }

    public IEnumerable<ToolMetadata> GetAllTools()
    {
        return _tools;
    }

    /// <summary>
    /// 将来的にツールを動的に登録するためのメソッド（現在は未実装）
    /// </summary>
    public void RegisterTool(ToolMetadata tool)
    {
        _tools.Add(tool);
    }
}
