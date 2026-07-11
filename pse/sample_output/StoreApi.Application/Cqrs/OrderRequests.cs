using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using MediatR;
using StoreApi.Domain.Entities;
using StoreApi.Application.Interfaces;

namespace StoreApi.Application.Cqrs;

public sealed record GetAllOrderQuery() : IRequest<IEnumerable<Order>>;

public sealed record GetOrderByIdQuery(Guid Id) : IRequest<Order?>;

public sealed record CreateOrderCommand(Order Entity) : IRequest<Order>;

public sealed record UpdateOrderCommand(Guid Id, Order Entity) : IRequest<bool>;

public sealed record DeleteOrderCommand(Guid Id) : IRequest<bool>;

public sealed class GetAllOrderQueryHandler : IRequestHandler<GetAllOrderQuery, IEnumerable<Order>>
{
    private readonly IOrderService _service;

    public GetAllOrderQueryHandler(IOrderService service)
    {
        _service = service;
    }

    public Task<IEnumerable<Order>> Handle(GetAllOrderQuery request, CancellationToken cancellationToken)
    {
        return Task.FromResult(_service.GetAll());
    }
}

public sealed class GetOrderByIdQueryHandler : IRequestHandler<GetOrderByIdQuery, Order?>
{
    private readonly IOrderService _service;

    public GetOrderByIdQueryHandler(IOrderService service)
    {
        _service = service;
    }

    public Task<Order?> Handle(GetOrderByIdQuery request, CancellationToken cancellationToken)
    {
        return Task.FromResult(_service.GetById(request.Id));
    }
}

public sealed class CreateOrderCommandHandler : IRequestHandler<CreateOrderCommand, Order>
{
    private readonly IOrderService _service;

    public CreateOrderCommandHandler(IOrderService service)
    {
        _service = service;
    }

    public Task<Order> Handle(CreateOrderCommand request, CancellationToken cancellationToken)
    {
        return Task.FromResult(_service.Create(request.Entity));
    }
}

public sealed class UpdateOrderCommandHandler : IRequestHandler<UpdateOrderCommand, bool>
{
    private readonly IOrderService _service;

    public UpdateOrderCommandHandler(IOrderService service)
    {
        _service = service;
    }

    public Task<bool> Handle(UpdateOrderCommand request, CancellationToken cancellationToken)
    {
        return Task.FromResult(_service.Update(request.Id, request.Entity));
    }
}

public sealed class DeleteOrderCommandHandler : IRequestHandler<DeleteOrderCommand, bool>
{
    private readonly IOrderService _service;

    public DeleteOrderCommandHandler(IOrderService service)
    {
        _service = service;
    }

    public Task<bool> Handle(DeleteOrderCommand request, CancellationToken cancellationToken)
    {
        return Task.FromResult(_service.Delete(request.Id));
    }
}
