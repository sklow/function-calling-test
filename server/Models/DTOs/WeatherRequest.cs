using System.ComponentModel.DataAnnotations;
using System.ComponentModel;

namespace FunctionCallingServer.Models.DTOs;

/// <summary>
/// 天気情報取得リクエストの DTO
/// </summary>
public class WeatherRequest
{
    /// <summary>
    /// 都市名
    /// </summary>
    [Required(ErrorMessage = "都市名は必須です")]
    [Description("都市名")]
    public string City { get; set; } = string.Empty;

    /// <summary>
    /// 温度の単位（metric または imperial）
    /// </summary>
    [Description("温度の単位")]
    public string Unit { get; set; } = "metric";
}
