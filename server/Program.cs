// ASP.NET Core Minimal API エントリーポイント

using FunctionCallingServer.Models.DTOs;
using FunctionCallingServer.Services;
using FunctionCallingServer.Tools;

// Web アプリケーションビルダーの作成
var builder = WebApplication.CreateBuilder(args);

// ===== サービスの登録 =====

// CORS ポリシーの設定
// Python クライアントからのアクセスを許可
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowPythonClient", policy =>
    {
        policy.WithOrigins("http://localhost:*") // localhost の任意のポートを許可
              .SetIsOriginAllowedToAllowWildcardSubdomains()
              .AllowAnyMethod()  // すべての HTTP メソッドを許可
              .AllowAnyHeader(); // すべてのヘッダーを許可
    });
});

// Swagger/OpenAPI の設定
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo
    {
        Title = "Function Calling Server",
        Version = "v1",
        Description = "Gemma 3 用のツール提供 API"
    });
});

// ツールレジストリサービスを Singleton として登録
// アプリケーションライフタイム全体で同一のインスタンスを使用
builder.Services.AddSingleton<IToolRegistry, ToolRegistry>();

// WeatherTool を Scoped として登録
// リクエストごとに新しいインスタンスを生成
builder.Services.AddScoped<IWeatherTool, WeatherTool>();

// ===== アプリケーションのビルド =====
var app = builder.Build();

// ===== ミドルウェアの構成 =====

// Development 環境では Swagger UI を有効化
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(options =>
    {
        options.SwaggerEndpoint("/swagger/v1/swagger.json", "Function Calling Server v1");
        options.RoutePrefix = "swagger"; // Swagger UI のパスを /swagger に設定
    });
}

// HTTPS リダイレクト
app.UseHttpsRedirection();

// CORS ミドルウェアの追加
app.UseCors("AllowPythonClient");

// ===== エンドポイントの定義 =====

// ヘルスチェック用のシンプルな GET / エンドポイント
app.MapGet("/", () => new
{
    status = "healthy",
    message = "Function Calling Server is running",
    timestamp = DateTime.UtcNow
})
.WithName("HealthCheck")
.WithOpenApi();

// ツールレジストリエンドポイント
// LLM が利用可能なツール一覧を取得
app.MapGet("/tools", (IToolRegistry toolRegistry) =>
{
    var tools = toolRegistry.GetAllTools();
    return Results.Ok(new
    {
        tools = tools,
        count = tools.Count()
    });
})
.WithName("GetTools")
.WithOpenApi(operation => new(operation)
{
    Summary = "利用可能なツール一覧を取得",
    Description = "LLM が Function Calling で使用できるツールのメタデータを返します"
});

// 天気情報取得エンドポイント
// 指定した都市の天気情報を取得
app.MapPost("/tools/get_weather", async (WeatherRequest request, IWeatherTool weatherTool) =>
{
    try
    {
        // リクエストのバリデーション
        // DataAnnotations による自動バリデーションは Minimal API では行われないため手動チェック
        var validationContext = new System.ComponentModel.DataAnnotations.ValidationContext(request);
        var validationResults = new List<System.ComponentModel.DataAnnotations.ValidationResult>();

        if (!System.ComponentModel.DataAnnotations.Validator.TryValidateObject(
            request, validationContext, validationResults, true))
        {
            var errors = validationResults
                .Select(r => r.ErrorMessage)
                .Where(e => e != null);

            return Results.BadRequest(new
            {
                error = "バリデーションエラー",
                details = errors
            });
        }

        // WeatherTool を使用して天気情報を取得
        var response = await weatherTool.GetWeatherAsync(request);

        return Results.Ok(response);
    }
    catch (Exception ex)
    {
        // 内部エラーの場合は 500 を返す
        return Results.Problem(
            detail: ex.Message,
            statusCode: 500,
            title: "内部サーバーエラー"
        );
    }
})
.WithName("GetWeather")
.WithOpenApi(operation => new(operation)
{
    Summary = "天気情報を取得",
    Description = "指定した都市の現在の天気情報を取得します。ダミーデータを返します。"
});

// アプリケーションの実行
app.Run();
