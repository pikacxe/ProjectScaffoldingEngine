using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using MediatR;
using StoreApi.Domain.Entities;
using StoreApi.Application.Interfaces;

namespace StoreApi.Application.Cqrs;

public sealed record GetAllOrderItemQuery() : IRequest<IEnumerable<OrderItem>>;

public sealed record GetOrderItemByIdQuery(Guid Id) : IRequest<OrderItem?>;

public sealed record CreateOrderItemCommand(OrderItem Entity) : IRequest<OrderItem>;

public sealed record UpdateOrderItemCommand(Guid Id, OrderItem Entity) : IRequest<bool>;

public sealed record DeleteOrderItemCommand(Guid Id) : IRequest<bool>;

public sealed class GetAllOrderItemQueryHandler : IRequestHandler<GetAllOrderItemQuery, IEnumerable<OrderItem>>
{
    private readonly IOrderItemService _service;

    public GetAllOrderItemQueryHandler(IOrderItemService service)
    {
        _service = service;
    }

    public Task<IEnumerable<OrderItem>> Handle(GetAllOrderItemQuery request, CancellationToken cancellationToken)
    {
        return Task.FromResult(_service.GetAll());
    }
}

public sealed class GetOrderItemByIdQueryHandler : IRequestHandler<GetOrderItemByIdQuery, OrderItem?>
{
    private readonly IOrderItemService _service;

    public GetOrderItemByIdQueryHandler(IOrderItemService service)
    {
        _service = service;
    }

    public Task<OrderItem?> Handle(GetOrderItemByIdQuery request, CancellationToken cancellationToken)
    {
        return Task.FromResult(_service.GetById(request.Id));
    }
}

public sealed class CreateOrderItemCommandHandler : IRequestHandler<CreateOrderItemCommand, OrderItem>
{
    private readonly IOrderItemService _service;

    public CreateOrderItemCommandHandler(IOrderItemService service)
    {
        _service = service;
    }

    public Task<OrderItem> Handle(CreateOrderItemCommand request, CancellationToken cancellationToken)
    {
        return Task.FromResult(_service.Create(request.Entity));
    }
}

public sealed class UpdateOrderItemCommandHandler : IRequestHandler<UpdateOrderItemCommand, bool>
{
    private readonly IOrderItemService _service;

    public UpdateOrderItemCommandHandler(IOrderItemService service)
    {
        _service = service;
    }

    public Task<bool> Handle(UpdateOrderItemCommand request, CancellationToken cancellationToken)
    {
        return Task.FromResult(_service.Update(request.Id, request.Entity));
    }
}

public sealed class DeleteOrderItemCommandHandler : IRequestHandler<DeleteOrderItemCommand, bool>
{
    private readonly IOrderItemService _service;

    public DeleteOrderItemCommandHandler(IOrderItemService service)
    {
        _service = service;
    }

    public Task<bool> Handle(DeleteOrderItemCommand request, CancellationToken cancellationToken)
    {
        return Task.FromResult(_service.Delete(request.Id));
    }
}
