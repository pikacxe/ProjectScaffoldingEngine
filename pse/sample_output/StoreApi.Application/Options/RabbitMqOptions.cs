namespace StoreApi.Application.Options;

public class RabbitMqOptions
{
    public string Host { get; set; } = string.Empty;
    public string Username { get; set; } = "guest";
    public string Password { get; set; } = "guest";
}
