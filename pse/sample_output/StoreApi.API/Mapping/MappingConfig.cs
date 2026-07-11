using Mapster;
using StoreApi.API.Dtos;
using StoreApi.Domain.Entities;

namespace StoreApi.API.Mapping;

public static class MappingConfig
{
    public static void Register()
    {
        TypeAdapterConfig<Order, OrderDto>.NewConfig();
        TypeAdapterConfig<OrderDto, Order>.NewConfig();
        TypeAdapterConfig<OrderItem, OrderItemDto>.NewConfig();
        TypeAdapterConfig<OrderItemDto, OrderItem>.NewConfig();
    }
}
