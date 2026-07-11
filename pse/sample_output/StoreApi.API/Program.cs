using Serilog;
using FluentValidation;
using FluentValidation.AspNetCore;
using Mapster;
using MapsterMapper;
using StoreApi.API.Mapping;
using StoreApi.Application.Interfaces;
using StoreApi.Application.Services;
using StoreApi.Application.Cqrs;
using StoreApi.Domain.Repositories;
using StoreApi.Infrastructure.Repositories;
using StoreApi.Application.Options;
using Microsoft.EntityFrameworkCore;
using StoreApi.Infrastructure.Persistence;

var builder = WebApplication.CreateBuilder(args);

builder.Host.UseSerilog((context, services, loggerConfiguration) =>
    loggerConfiguration
        .ReadFrom.Configuration(context.Configuration)
        .ReadFrom.Services(services)
        .WriteTo.Console());


builder.Services.AddControllers();

builder.Services.AddFluentValidationAutoValidation();
builder.Services.AddValidatorsFromAssemblyContaining<Program>();

MappingConfig.Register();
builder.Services.AddMapster();

builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services.AddScoped<IOrderItemService, OrderItemService>();

builder.Services.AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<GetAllOrderQueryHandler>());

builder.Services.AddSingleton<IOrderRepository, OrderRepository>();
builder.Services.AddSingleton<IOrderItemRepository, OrderItemRepository>();

builder.Services.Configure<DatabaseOptions>(builder.Configuration.GetSection("Database"));
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("Database")));

builder.Services.Configure<RedisOptions>(builder.Configuration.GetSection("Redis"));
builder.Services.AddStackExchangeRedisCache(options =>
    options.Configuration = builder.Configuration.GetConnectionString("Redis"));

var app = builder.Build();

app.MapControllers();

app.Run();
