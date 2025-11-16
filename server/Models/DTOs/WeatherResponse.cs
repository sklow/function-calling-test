using System.ComponentModel;

namespace FunctionCallingServer.Models.DTOs;

/// <summary>
/// 天気情報取得レスポンスの DTO
/// </summary>
public class WeatherResponse
{
    /// <summary>
    /// 気温
    /// </summary>
    [Description("気温")]
    public double Temp { get; set; }

    /// <summary>
    /// 天気の説明
    /// </summary>
    [Description("天気の説明")]
    public string Desc { get; set; } = string.Empty;
}
