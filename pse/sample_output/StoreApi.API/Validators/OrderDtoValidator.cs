using FluentValidation;
using StoreApi.API.Dtos;

namespace StoreApi.API.Validators;

public class OrderDtoValidator : AbstractValidator<OrderDto>
{
    public OrderDtoValidator()
    {
        RuleFor(x => x.Id).NotEmpty();
        RuleFor(x => x.CreatedAt).NotEmpty();
        RuleFor(x => x.Status).NotEmpty();
    }
}
