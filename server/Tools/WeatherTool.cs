using FunctionCallingServer.Models.DTOs;

namespace FunctionCallingServer.Tools;

/// <summary>
/// 天気情報取得ツールのインターフェース
/// </summary>
public interface IWeatherTool
{
    /// <summary>
    /// 天気情報を非同期で取得
    /// </summary>
    /// <param name="request">天気情報取得リクエスト</param>
    /// <returns>天気情報レスポンス</returns>
    Task<WeatherResponse> GetWeatherAsync(WeatherRequest request);
}

/// <summary>
/// 天気情報取得ツールの実装
/// ダミーデータを返すが、実装は本格的に行う
/// </summary>
public class WeatherTool : IWeatherTool
{
    private readonly ILogger<WeatherTool> _logger;

    /// <summary>
    /// 主要都市の天気データマップ
    /// </summary>
    private static readonly Dictionary<string, (double MetricTemp, string Desc)> CityWeatherMap = new()
    {
        { "tokyo", (15.5, "曇り時々晴れ") },
        { "osaka", (17.2, "晴れ") },
        { "yokohama", (16.0, "曇り") },
        { "nagoya", (14.8, "晴れ") },
        { "sapporo", (8.3, "雪") },
        { "fukuoka", (18.5, "晴れ") },
        { "new york", (10.0, "曇り") },
        { "london", (12.5, "雨") },
        { "paris", (11.8, "曇り") },
        { "berlin", (9.2, "曇り時々雨") },
        { "sydney", (22.0, "晴れ") },
        { "singapore", (28.5, "曇り時々雨") },
        { "seoul", (10.5, "晴れ") },
        { "beijing", (8.0, "曇り") },
        { "shanghai", (15.0, "雨") }
    };

    /// <summary>
    /// コンストラクタ
    /// </summary>
    /// <param name="logger">ロガー</param>
    public WeatherTool(ILogger<WeatherTool> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// 天気情報を非同期で取得
    /// 都市名に基づいてダミーの天気情報を生成
    /// </summary>
    /// <param name="request">天気情報取得リクエスト</param>
    /// <returns>天気情報レスポンス</returns>
    public Task<WeatherResponse> GetWeatherAsync(WeatherRequest request)
    {
        _logger.LogInformation("天気情報取得リクエスト: City={City}, Unit={Unit}",
            request.City, request.Unit);

        // 都市名を正規化（小文字に変換、前後の空白を削除）
        var normalizedCity = request.City.Trim().ToLowerInvariant();

        // 主要都市のマップから天気データを取得
        if (CityWeatherMap.TryGetValue(normalizedCity, out var weatherData))
        {
            var (metricTemp, desc) = weatherData;
            var temp = ConvertTemperature(metricTemp, request.Unit);

            _logger.LogInformation("天気情報を返却: City={City}, Temp={Temp}, Desc={Desc}",
                request.City, temp, desc);

            return Task.FromResult(new WeatherResponse
            {
                Temp = temp,
                Desc = desc
            });
        }

        // マップにない都市の場合は疑似ランダムデータを生成
        var (pseudoTemp, pseudoDesc) = GeneratePseudoWeather(normalizedCity);
        var convertedTemp = ConvertTemperature(pseudoTemp, request.Unit);

        _logger.LogInformation("疑似天気情報を生成: City={City}, Temp={Temp}, Desc={Desc}",
            request.City, convertedTemp, pseudoDesc);

        return Task.FromResult(new WeatherResponse
        {
            Temp = convertedTemp,
            Desc = pseudoDesc
        });
    }

    /// <summary>
    /// 温度を指定された単位に変換
    /// </summary>
    /// <param name="metricTemp">摂氏温度</param>
    /// <param name="unit">温度単位（metric または imperial）</param>
    /// <returns>変換された温度</returns>
    private static double ConvertTemperature(double metricTemp, string unit)
    {
        // imperial の場合は華氏に変換
        if (unit.Equals("imperial", StringComparison.OrdinalIgnoreCase))
        {
            // 華氏 = 摂氏 × 9/5 + 32
            return Math.Round(metricTemp * 9.0 / 5.0 + 32.0, 1);
        }

        // metric の場合はそのまま返す
        return Math.Round(metricTemp, 1);
    }

    /// <summary>
    /// 都市名のハッシュ値を使用して疑似ランダムな天気データを生成
    /// </summary>
    /// <param name="city">正規化された都市名</param>
    /// <returns>疑似的な気温と天気の説明</returns>
    private static (double Temp, string Desc) GeneratePseudoWeather(string city)
    {
        // 都市名のハッシュ値を計算
        var hashCode = city.GetHashCode();

        // ハッシュ値をシードとして使用し、一定の疑似ランダム性を持たせる
        var random = new Random(hashCode);

        // 気温を -10°C ~ 35°C の範囲で生成
        var temp = random.Next(-100, 351) / 10.0; // -10.0 ~ 35.0

        // 天気の説明リスト
        var weatherDescriptions = new[]
        {
            "晴れ",
            "曇り",
            "雨",
            "雪",
            "晴れ時々曇り",
            "曇り時々晴れ",
            "曇り時々雨",
            "雨時々曇り"
        };

        // ハッシュ値から天気の説明を選択
        var descIndex = Math.Abs(hashCode) % weatherDescriptions.Length;
        var desc = weatherDescriptions[descIndex];

        return (temp, desc);
    }
}
